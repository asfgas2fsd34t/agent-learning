# 练习 19：Agent 调试、评测与性能优化

使用固定评测案例，计算正确性、结构通过率、延迟和错误分类。默认不调用模型，先学习评测框架。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/Agent开发实战/11-agent-evaluation
python -m uv run agent-evaluate
python -m uv run python -m unittest discover -s tests -v
```

对应笔记：[12 调试、评测与性能优化](../../../notes/Agent开发实战/12-调试评测与性能优化.md)
