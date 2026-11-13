# 开发指南

## 环境

- 平台：Windows。
- Python：`pyproject.toml` 要求 `>=3.12`；CI 使用 Python 3.12。
- 环境管理：使用 `uv` 和仓库锁文件。

```powershell
uv sync --frozen
uv run python main.py
```

## 本地验证

```powershell
uv run python -m compileall -q app module tasks utils scripts main.py main_dev.py updater.py
uv run pytest --collect-only -q
uv run pytest -ra
uv run ruff check app module tasks utils scripts tests main.py main_dev.py updater.py
```

应用配置加载会读取工作目录中的 `config.yaml`，并可能创建配置备份。若该文件包含个人设置，请在排除 `config.yaml*`、`config_backup`、日志和缓存的隔离副本运行测试；不要复制、提交或打印个人配置内容。每次 pytest 使用新的 `--basetemp`。

## 开发模式

```powershell
uv run python main_dev.py
uv run python main_dev.py --no-reload
```

默认模式支持文件变化重载；`--no-reload` 保留手动 `Ctrl+R` 重载。

## 翻译

```powershell
uv run python scripts/translation_files_build.py
uv run python scripts/translation_files_compile.py
```

维护者与 AI 代理的完整边界和验证顺序见[项目文档索引](../../../docs/INDEX.md)。
