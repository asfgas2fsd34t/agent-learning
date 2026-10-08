# 15 RAG（检索增强生成）

> 来源：Spring AI 官方文档 `api/retrieval-augmented-generation.html` + `api/etl-pipeline.html`（1.1.x）。前置：02 章 Advisor、04 章 Prompt。

## 学习目标

- 理解 RAG 的动机与"离线入库 + 在线检索"两半闭环
- 会用 ETL 管道（Reader→Transformer→Writer）把文档写进向量库
- 掌握两条在线路线：QuestionAnswerAdvisor（一行版）与 RetrievalAugmentationAdvisor（模块化）
- 了解四阶段模块（Pre-Retrieval / Retrieval / Post-Retrieval / Generation）的组件

## 1. 核心心智模型

```text
RAG = 让模型"开卷考试"：回答前先从你的知识库里捞相关材料塞进 prompt
解决 LLM 三大痛点：长文本记不住、知识不过时、一本正经胡说（幻觉）

两半闭环：
  离线（ETL）：读文档 → 分块 → 向量化 → 存向量库
  在线（RAG）：用户问题 → 向量检索 → 材料拼进 prompt → 生成回答
```

Spring AI 的实现：模块化 RAG 架构（受 "Modular RAG" 论文启发），要么用现成 Advisor，要么拿模块自己拼。

## 2. 离线半边：ETL Pipeline

三接口（Java 函数式风格的三件套）：

| 接口 | 函数式形态 | 方法 |
|------|-----------|------|
| DocumentReader | Supplier\<List\<Document\>\> | `read()` |
| DocumentTransformer | Function\<List\<Document\>, List\<Document\>\> | `transform()` |
| DocumentWriter | Consumer\<List\<Document\>\> | `write()` |

Document = 文本 + 元数据（+ 可选媒体）。

**一行 ETL**（PDF → 分块 → 入向量库）：

```java
vectorStore.accept(tokenTextSplitter.apply(pdfReader.get()));
// 或领域友好的写法
vectorStore.write(tokenTextSplitter.split(pdfReader.read()));
```

### 2.1 Readers（读取器）

JSON、Text、HTML(JSoup)、Markdown、PDF Page、PDF Paragraph、Tika(DOCX/PPTX 等)。示例：

```java
// JsonReader：指定哪些 key 作为正文
JsonReader jsonReader = new JsonReader(this.resource, "description", "content");
List<Document> docs = jsonReader.get();

// 还支持 JSON Pointer（RFC 6901）取嵌套片段
docs = jsonReader.get("/bikes/0");
```

⚠️ Reader/Writer 大多接受 Resource/资源模式，**不要直接用用户传入的 URL 构造**（安全风险）。

### 2.2 Transformers（转换器）

**TokenTextSplitter**（核心：按 token 分块，CL100K_BASE 编码）：

```java
TokenTextSplitter splitter = TokenTextSplitter.builder()
    .withChunkSize(1000)            // 每块 token 数
    .withMinChunkSizeChars(400)     // 块最小字符数
    .withMinChunkLengthToEmbed(10)  // 太短的不嵌入
    .withMaxNumChunks(5000)
    .withKeepSeparator(true)
    .build();
List<Document> chunks = splitter.apply(documents);

// 中文场景换中文标点
TokenTextSplitter cn = TokenTextSplitter.builder()
    .withChunkSize(800)
    .withPunctuationMarks(List.of('。', '？', '！', '\n'))
    .build();
```

**KeywordMetadataEnricher**（AI 抽关键词进元数据）：

```java
KeywordMetadataEnricher enricher = KeywordMetadataEnricher.builder(chatModel)
        .keywordCount(5)      // 写入 metadata["excerpt_keywords"]
        .build();
List<Document> enriched = enricher.apply(documents);
```

**SummaryMetadataEnricher**（AI 生成摘要进元数据，可带前后文）：

```java
@Bean
public SummaryMetadataEnricher summaryMetadata(OpenAiChatModel aiClient) {
    return new SummaryMetadataEnricher(aiClient,
        List.of(SummaryType.PREVIOUS, SummaryType.CURRENT, SummaryType.NEXT));
}
```

还有 ContentFormatTransformer 等。

### 2.3 Writers（写入器）

- **VectorStore**：`vectorStore.write(docs)`——向量化并入库（详见 vectordbs 页）
- **File**：写出文件（带文档标记、元数据处理）

## 3. 在线半边 A：QuestionAnswerAdvisor（一行版）

```xml
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-advisors-vector-store</artifactId>
</dependency>
```

```java
// 最简：挂上就自动"检索→拼进 prompt→回答"
ChatResponse response = ChatClient.builder(chatModel)
        .build().prompt()
        .advisors(QuestionAnswerAdvisor.builder(vectorStore).build())
        .user(userText)
        .call()
        .chatResponse();
```

检索参数定制（阈值 0.8、top 6）：

```java
var qaAdvisor = QuestionAnswerAdvisor.builder(vectorStore)
        .searchRequest(SearchRequest.builder().similarityThreshold(0.8d).topK(6).build())
        .build();
```

动态过滤表达式（运行时按 metadata 过滤，SQL 风格、跨向量库可移植）：

```java
String content = this.chatClient.prompt()
    .user("Please answer my question XYZ")
    .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "type == 'Spring'"))
    .call().content();
```

自定义模板（必须含 `{query}` 和 `{question_answer_context}` 两个占位符）：

```java
PromptTemplate customPromptTemplate = PromptTemplate.builder()
    .renderer(StTemplateRenderer.builder().startDelimiterToken('<').endDelimiterToken('>').build())
    .template("""
            <query>

            Context information is below.

			---------------------
			<question_answer_context>
			---------------------

			Given the context information and no prior knowledge, answer the query.

			Follow these rules:

			1. If the answer is not in the context, just say that you don't know.
			2. Avoid statements like "Based on the context..." or "The provided information...".
            """)
    .build();

QuestionAnswerAdvisor qaAdvisor = QuestionAnswerAdvisor.builder(vectorStore)
    .promptTemplate(customPromptTemplate)
    .build();
```

（`userTextAdvise()` 已废弃，用 `promptTemplate()`。）

## 4. 在线半边 B：RetrievalAugmentationAdvisor（模块化）

```xml
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-rag</artifactId>
</dependency>
```

### 4.1 Naive RAG

```java
Advisor retrievalAugmentationAdvisor = RetrievalAugmentationAdvisor.builder()
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.50)
                .vectorStore(vectorStore)
                .build())
        .build();

String answer = chatClient.prompt()
        .advisors(retrievalAugmentationAdvisor)
        .user(question)
        .call().content();
```

默认**不允许空上下文**（检索不到就让模型拒答）；允许空：

```java
.queryAugmenter(ContextualQueryAugmenter.builder()
        .allowEmptyContext(true)
        .build())
```

运行时过滤：

```java
.advisors(a -> a.param(VectorStoreDocumentRetriever.FILTER_EXPRESSION, "type == 'Spring'"))
```

### 4.2 Advanced RAG（加查询改写 + 后处理）

```java
Advisor retrievalAugmentationAdvisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(RewriteQueryTransformer.builder()
                .chatClientBuilder(chatClientBuilder.build().mutate())
                .build())
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.50)
                .vectorStore(vectorStore)
                .build())
        .build();
```

## 5. 四阶段模块（组件库）

```text
Pre-Retrieval（优化查询）→ Retrieval（捞文档）→ Post-Retrieval（加工文档）→ Generation（拼 prompt 生成）
```

### 5.1 Pre-Retrieval —— 查询转换与扩展

建议：QueryTransformer 的 ChatClient 用 **temperature=0.0**，保证改写稳定。

**CompressionQueryTransformer**（长对话压缩成独立查询）：

```java
Query query = Query.builder()
        .text("And what is its second largest city?")
        .history(new UserMessage("What is the capital of Denmark?"),
                new AssistantMessage("Copenhagen is the capital of Denmark."))
        .build();
QueryTransformer t = CompressionQueryTransformer.builder()
        .chatClientBuilder(chatClientBuilder).build();
Query transformed = t.transform(query);   // → "What is the second largest city of Denmark?"
```

**RewriteQueryTransformer**（啰嗦/模糊查询重写）：

```java
Query query = new Query("I'm studying machine learning. What is an LLM?");
QueryTransformer t = RewriteQueryTransformer.builder()
        .chatClientBuilder(chatClientBuilder).build();
```

**TranslationQueryTransformer**（翻译成嵌入模型支持的语言；已是目标语言则原样返回）：

```java
Query query = new Query("Hvad er Danmarks hovedstad?");
QueryTransformer t = TranslationQueryTransformer.builder()
        .chatClientBuilder(chatClientBuilder)
        .targetLanguage("english").build();
```

**MultiQueryExpander**（一个查询扩成多个语义变体，提高召回）：

```java
MultiQueryExpander queryExpander = MultiQueryExpander.builder()
    .chatClientBuilder(chatClientBuilder)
    .numberOfQueries(3)
    .build();
List<Query> queries = queryExpander.expand(new Query("How to run a Spring Boot app?"));
// 默认含原始查询；includeOriginal(false) 可关
```

### 5.2 Retrieval —— 检索与合并

**VectorStoreDocumentRetriever**（支持阈值、topK、元数据过滤；过滤可静态/动态）：

```java
DocumentRetriever retriever = VectorStoreDocumentRetriever.builder()
    .vectorStore(vectorStore)
    .similarityThreshold(0.73)
    .topK(5)
    .filterExpression(new FilterExpressionBuilder()
        .eq("genre", "fairytale")
        .build())
    .build();
List<Document> documents = retriever.retrieve(new Query("What is the main character of the story?"));
```

动态过滤（Supplier，多租户利器）：

```java
DocumentRetriever retriever = VectorStoreDocumentRetriever.builder()
    .vectorStore(vectorStore)
    .filterExpression(() -> new FilterExpressionBuilder()
        .eq("tenant", TenantContextHolder.getTenantIdentifier())
        .build())
    .build();
```

请求级过滤优先于检索器级：

```java
Query query = Query.builder()
    .text("Who is Anacletus?")
    .context(Map.of(VectorStoreDocumentRetriever.FILTER_EXPRESSION, "location == 'Whispering Woods'"))
    .build();
```

**ConcatenationDocumentJoiner**（多查询/多来源结果拼接，去重保首次，分数原样）：

```java
Map<Query, List<List<Document>>> documentsForQuery = ...
DocumentJoiner documentJoiner = new ConcatenationDocumentJoiner();
List<Document> documents = documentJoiner.join(documentsForQuery);
```

### 5.3 Post-Retrieval —— 文档后处理

`DocumentPostProcessor` 接口：重排序、去冗余、内容压缩（解决 lost-in-the-middle、上下文长度限制）。可插到生成前。

### 5.4 Generation —— 查询增强

**ContextualQueryAugmenter**（把检索内容拼进 prompt；默认空上下文拒答）：

```java
QueryAugmenter queryAugmenter = ContextualQueryAugmenter.builder().build();

// 允许空上下文（模型可凭自身知识答）
QueryAugmenter queryAugmenter = ContextualQueryAugmenter.builder()
        .allowEmptyContext(true)
        .build();
// promptTemplate() / emptyContextPromptTemplate() 可定制提示词
```

## 6. 与前文串联

- RAG 整个就是 02 章说的"Advisor 用于检索增强"的落地：两条路线都是 Advisor
- `FILTER_EXPRESSION` 的运行时参数 = `a.param(...)` 机制（02 章第 5 节）
- 动态过滤 Supplier + tenant = 09 章 ToolContext 多租户思路在检索侧的对应物
- `spring-ai-advisors-vector-store` 依赖同时提供 VectorStoreChatMemoryAdvisor（08 章长记忆）
- QueryTransformer 用 ChatClient 实现——又回到 01 章

## 7. 自测题

1. RAG 为什么能缓解幻觉？空上下文时默认行为是什么？
2. QuestionAnswerAdvisor 和 RetrievalAugmentationAdvisor 怎么选？
3. 多租户下怎么保证检索不串库？
4. ETL 一行代码 `vectorStore.write(tokenTextSplitter.split(pdfReader.read()))` 三个方法各属哪个接口？

## 8. 生产边界

- QueryTransformer 的模型 temperature 调 0
- 分块大小（chunkSize）是召回质量第一参数，按文档类型调；中文换中文标点
- topK/相似度阈值需要评测调参，别拍脑袋
- 空上下文策略要想清楚：拒答 vs 凭模型知识答（客服场景通常拒答更安全）
- 元数据过滤是多租户隔离的关键，检索器必须带 tenant 过滤
- Reader 不要直接吃用户 URL（安全）
- 向量库选型看 vectordbs 页（PG 用户直接看 pgvector）
