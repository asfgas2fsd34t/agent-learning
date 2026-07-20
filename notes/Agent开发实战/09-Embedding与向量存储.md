# 09 Embedding 与向量存储

## 本课目标

把文本变成可比较的向量只是第一步。工程上还要保证模型版本、维度、距离函数、metadata 过滤和索引更新策略一致：

```text
chunk -> embedding model -> vector + metadata -> index
query -> 同一个 embedding model -> query vector -> search/filter -> Documents
```

## 1. Embeddings 接口

LangChain 的核心契约是：

```python
class Embeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
```

文档向量和查询向量必须来自兼容的模型空间。实践中的 `HashEmbeddings` 通过字符片段和哈希生成确定性向量，方便离线测试接口，但它没有真正理解语义，不能据此判断生产模型质量。

## 2. 向量空间的约束

需要固定并记录：

```text
embedding_model、model_version、dimension、distance_metric、normalization
```

不同模型的向量即使都是 `list[float]`，维度或空间含义也可能不同，不能混存后直接比较。模型升级可能改变召回结果，通常需要新建索引、离线评测，再切换 alias，而不是直接覆盖线上向量。

常见距离：

- Cosine：关注方向，常用于归一化语义向量。
- Dot product：受向量长度影响，模型和库要约定是否归一化。
- Euclidean：关注几何距离，尺度变化会影响排序。

不要只记住“越小越近”或“越大越近”，先确认向量库 API 返回值的含义。

## 3. VectorStore 的职责边界

```python
store.add_documents(documents)
docs = store.similarity_search("Runnable 是什么", k=3)
```

VectorStore 负责向量写入、索引和相似度查询；它不负责：

- 判断用户是否有权限
- 决定答案是否可信
- 处理业务事务
- 自动删除旧版本
- 证明召回结果一定相关

`InMemoryVectorStore` 进程退出即丢失，适合学习和单元测试。生产库还要考虑持久化、备份、索引重建、过滤表达式、租户隔离、删除一致性和监控。

## 4. 过滤和权限顺序

安全的检索概念上应是：

```text
可信身份 -> 构造 tenant/visibility filter
         -> 在向量库查询中应用过滤
         -> 对候选结果再次做服务端校验
         -> 交给模型
```

不要先取全库 top-k，再让模型“挑出允许的内容”。这既可能泄露数据，也可能因为无权限文档占据 top-k 导致真正相关文档根本没有机会出现。

## 5. 写入、更新和删除

每个向量记录应有稳定 ID，例如：

```text
{document_id}:{version}:{chunk_index}
```

写入前先根据 content hash 去重；版本替换要保证旧版本不会被召回；删除操作要能按 document_id 清理所有 chunk。批量写入建议记录成功数、失败 ID 和重试状态，不能只返回“入库完成”。

## 6. 评估 Embedding，不要只看 Demo

准备标注问题集：

```text
question -> 相关 document_id/chunk_id
```

比较不同模型和切分策略的 Recall@k、MRR、nDCG，并观察：

- 同义改写是否召回同一证据
- 数字、日期、产品 ID 是否准确
- 权限过滤后是否仍有足够候选
- 新旧版本是否混召

语义向量对精确编号、金额、日期不一定可靠，实际系统常需要关键词检索或混合检索。

## 7. practice/13 的代码如何阅读

对应代码：[practice/13-vector-store](../../practice/13-vector-store/README.md)

`build_store` 使用 `InMemoryVectorStore(HashEmbeddings())` 写入两份 Document，测试查询 Runnable 时检查返回的 source。学习重点是 `Embeddings` 的两个方法和 VectorStore 的调用边界，不是哈希向量的语义能力。

## 8. 可执行实验

1. 把 `dimensions` 改为 32，观察同一 store 是否还能复用旧向量。
2. 查询 `Runnable`、`退款` 和完全无关的词，打印 top-k 和 metadata。
3. 为文档增加 `tenant_id`，设计“查询前过滤”而不是查询后过滤。
4. 添加一个重复 chunk，观察为什么需要稳定 ID 或 hash 去重。

## 9. 自测

1. 为什么 `embed_query` 和 `embed_documents` 必须兼容？
2. 模型升级后为什么通常要重建索引？
3. 相似度排序为什么不能替代权限过滤？
4. VectorStore 和关系数据库各自适合保存什么？
5. 对金额、日期、订单号，为什么可能需要混合检索？

## 官方资料

- [Embeddings](https://docs.langchain.com/oss/python/integrations/text_embedding)
- [Vector stores](https://docs.langchain.com/oss/python/integrations/vectorstores)
