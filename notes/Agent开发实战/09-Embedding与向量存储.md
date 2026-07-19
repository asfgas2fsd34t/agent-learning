# 09 Embedding 与向量存储

## 学习目标

理解文本如何变成向量、相似度检索如何工作，以及向量数据库与关系数据库的职责差异。

## Embedding

Embedding 模型把文本映射为固定维度向量：

```text
"Runnable 是统一接口" -> [0.12, -0.31, ...]
```

语义相近的文本通常在向量空间中距离更近。维度由 Embedding 模型确定，不是开发者随意选择。

## 相似度

常见指标包括余弦相似度、点积和欧氏距离。必须遵循向量库和模型的推荐方式，不能在不同 Embedding 模型生成的向量之间直接比较。

## InMemoryVectorStore

```python
store = InMemoryVectorStore(embedding=embeddings)
store.add_documents(documents)
results = store.similarity_search("Runnable 是什么", k=3)
```

它适合学习和测试，进程重启后数据消失。生产向量库还要考虑持久化、索引、备份、租户隔离和增量更新。

## Metadata 过滤

相似度不等于权限。检索前必须根据服务端身份限制租户、部门和文档等级。不能先检索所有数据，再让模型决定哪些可以展示。

## 更新策略

文档更新时应使用稳定 `document_id/version/chunk_index`，删除旧版本再写入新版本，避免同一内容重复召回。

## 对应实践

[practice/13-vector-store](../../practice/13-vector-store/README.md) 使用 `InMemoryVectorStore` 和可重复的教学 Embedding 验证写入、检索和元数据。教学 Embedding 只用于理解接口，不代表生产语义效果。

## 自测

1. token 维度与 Embedding 维度是什么关系？
2. 为什么不能混用不同 Embedding 模型的向量？
3. 向量相似为什么不能代替权限过滤？

## 官方资料

- [Embeddings](https://docs.langchain.com/oss/python/integrations/text_embedding)
- [Vector stores](https://docs.langchain.com/oss/python/integrations/vectorstores)

