# 练习 03：安全的写操作 Tool

这个练习使用模拟退款展示高风险写操作的三个核心控制：

- 权限校验
- 幂等控制
- 订单累计退款金额校验，防止更换幂等键绕过业务限制
- Human-in-the-loop
- `UNKNOWN` 状态和外部结果对账

## 关键设计

模型最多生成订单号候选和退款金额。幂等键由请求入口或业务服务生成，是否有退款权限、是否已经人工审批，由应用程序创建的 `ExecutionContext` 提供，不能由模型参数决定。

```python
result = execute_refund_tool(
    model_arguments,
    context=ExecutionContext(
        can_refund=current_user.can_refund,
        human_approved=approval_service.is_approved(request_id),
        idempotency_key=request.idempotency_key,
    ),
    service=refund_service,
)
```

## 运行测试

在仓库根目录同步 workspace：

```powershell
python -m uv sync --all-packages
```

进入本练习并运行：

```powershell
cd practice/03-safe-write-tool
python -m uv run python -m unittest discover -s tests -v
```

练习使用内存模拟退款记录，不会调用真实支付系统。
