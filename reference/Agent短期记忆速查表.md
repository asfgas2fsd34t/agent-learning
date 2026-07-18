# Agent 短期记忆速查表

## 核心事实

```text
大模型 API 本身通常无状态
Memory 由应用程序保存
每次调用前重新加载相关历史
历史消息最终仍要放入上下文窗口
```

## 最小流程

```text
conversation_id
-> 查询最近消息
-> system + history + 当前 user
-> 调用模型
-> 保存 user 和 assistant
```

## 生产字段

- message_id
- conversation_id
- user_id 和 tenant_id
- role 和 content
- status
- created_at
- token_count
- request_id

## 关键限制

- 不能无限加载全部历史
- 不同用户和租户必须隔离
- 敏感信息需要脱敏和生命周期管理
- 消息保存要处理重复提交和失败状态
- 长历史需要裁剪、摘要或相关性检索
