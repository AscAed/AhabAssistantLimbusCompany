# 构建指南

使用 Windows 和 Python 3.12 环境，先按锁文件安装依赖：

```powershell
uv sync --frozen
```

Release 路径会同时构建主程序和更新器、复制资源并生成压缩包：

```powershell
uv run python scripts/build.py --version 1.0.9
```

构建脚本启动时会递归删除 `dist/`。运行前确认该目录不存在，或使用不含用户制品的隔离副本。脚本还需要系统可用的 `7z`。构建结果保留为本地产物，不提交到 Git。

配置与验证边界见[开发指南](develop_guide.md)和[项目文档索引](../../../docs/INDEX.md)。
