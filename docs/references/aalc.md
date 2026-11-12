# AALC 本地参考实现分析

## 检出身份与边界

- 仓库：`E:\PUBLIC\Project\AALC\Source Code\AhabAssistantLimbusCompany`
- 分支：`main`，与 `origin/main` 对齐；审阅时工作区干净。
- HEAD：`2fcb1b4620108c9bb0cf138f82790dd13f46356c`
- 标签：`V1.6.1`、`V1.6.1-beta.15`
- 许可证：GNU AGPL v3，见 `LICENSE`。
- 审阅类型：静态代码与仓库文件审阅；未在此检出运行测试、构建程序或连接真实游戏。结论仅对应上述 SHA。
- 测试检索：找到 3 个 pytest 文件：`tests/test_config_schema.py`、`tests/test_theme_pack_catalog.py`、`tests/unit/module/logger/test_import_behavior.py`。这能证明存在针对性自动化测试，不能证明完整任务流或打包运行正确。

## 架构与实现

### UI、配置与启动

项目是面向 Windows 的 Python 桌面应用。`app/` 负责 PySide UI，`module/` 提供配置、自动化、OCR、资源同步和系统服务，`tasks/` 承载日常及 Mirror 流程。依赖与打包入口分别见 `pyproject.toml`、`main.py`、`main.spec` 和 `scripts/build.py`。

顶层 `ConfigModel` 的字段由 example YAML 提供默认值，并由类型模型校验：`module/config/config.py:24-53`、`module/config/config_typing.py:207`。这不覆盖嵌套 `TeamSetting` 的所有默认值；它仍在模型中定义多项默认值，并被 `ConfigModel.teams` 使用：`module/config/config_typing.py:6-24,123,195-204,546`。配置迁移也会读取 `TeamSetting()` 的默认值：`module/config/config.py:158-170`。

配置模块启动一个延迟写盘线程，并将短时间内的延迟保存请求合并。该路径不构成所有写盘都串行或耐久完成的保证：`save(instant=True)` 与 `flush()` 可以直接写盘；退出时的 `flush()` 不等待已排队或正在执行的后台写盘，目标文件直接以写模式打开。相关实现：`module/config/config.py:328-338,479-537`。

`tests/test_config_schema.py:49-67` 检查模型字段与 example YAML 的字段集合相同，并禁止在模型里重复声明默认值。这使新增字段更容易被发现，但该测试不覆盖历史配置迁移后的值保真。

### 输入、截图、识别与任务流

`module/automation/automation.py:40-62,345-428` 把输入后端选择、截图调用和目标查找收在 `Automation` 边界。Windows 输入实现分别包含前台、消息输入和窗口移动等后端；截图实现根据模拟器/窗口模式选择 GDI、ADB、MuMu 或 PyAutoGUI 路径，捕获失败时返回 `None`。相关位置：`module/automation/input_handlers/input.py:141,317,686`、`module/automation/screenshot.py:16-64`。

核心 Mirror 工作流位于 `tasks/mirror/mirror.py`，商店逻辑位于 `tasks/mirror/in_shop.py`，路线识别和规划位于 `tasks/mirror/search_road.py`。职责上可区分任务状态推进、商店决策和路线图处理；执行细节仍集中在较大的任务模块中。

`tasks/base/retry.py:125-152` 为卡死监控提供可配置超时和下限，并在超时时尝试重启游戏。任务流程中仍有 `while True` 与截图重试循环，例如 `tasks/mirror/mirror.py:146,240`、`tasks/mirror/in_shop.py:76,148`。外层 stall timeout 不能自动证明每个内层等待都能被定期检查或安全中止。

停止路径使用 `QThread.terminate()`：`app/farming_interface.py:760-763`；线程重写 `terminate()`，并在文档注释中说明强制终止不会释放线程持有的 `RLock`，随后重置自动化锁：`tasks/base/script_task_scheme.py:452-488`。这证明实现选择了强制终止与锁重置补救，不证明线程中其他游戏输入、文件或系统状态都能恢复。当前维护 Fork 是否已替换此路径由后续当前代码审计确认；不可把参考仓库的锁重置补救直接搬入。

### 资源同步与更新

`module/resource_sync/service.py:261-355` 按优先顺序检查候选资源源；捕获 `requests.RequestException`（包含 `raise_for_status()` 产生的 HTTP 状态异常）后切换来源，并为请求设置超时。`build_sync_plan()` 比较远端清单和本地文件，使用 SHA-256 判断变更，并显式生成新增、更新、删除清单：`module/resource_sync/service.py:440-473`。

整包下载校验大小和 SHA-256，解压前检查成员路径，拒绝绝对路径和 `..` 穿越；逐个复制文件前验证解压文件哈希，但此路径未按 `entry.size` 校验每个文件，也未在复制后再次校验目标文件。实现位置：`module/resource_sync/service.py:524-557,652-660`、`utils/archive_7z.py:144-166`。清单中的删除项最终会从受管资源目录删除：`module/resource_sync/service.py:663-674`；生产中是否只允许受管资源进入该目录，仍需结合清单生成和目录边界验证。

清单模型拒绝未知字段并规范化文件路径类型，但 `ResourceFileEntry.from_dict()` 未在该入口检查路径是否为安全相对路径：`module/resource_sync/manifest.py:26-63,149-159`。资源计划和落盘使用清单路径拼接本地目录：`module/resource_sync/service.py:449-464,652-674`。归档成员路径校验不能单独证明清单条目路径也受限；任何复用都应先验证 manifest 路径规范化、根目录包含关系和删除边界。

`ResourceSyncWorker` 使用 `QThread` 执行检查/计划/应用，将进度和失败通过信号回传 UI：`module/resource_sync/worker.py:36-46,112-189`。这有助于隔离耗时网络和文件操作，但本次未追踪整个用户确认与资源更新事务的运行时恢复行为。

### 测试、CI 与发布

当前自动化测试偏向配置契约、资源目录规则和日志导入行为。三份测试源码没有覆盖 Mirror 全程、输入设备行为、真实 OCR、资源同步事务或发布后的应用启动。

仓库含 GitHub Actions 工作流、PyInstaller spec、release 脚本和 updater 代码。本次审阅确认这些入口存在，但没有端到端验证更新安装、打包文件清理、应用签名或发布制品运行。

## 工程质量判断

| 领域 | 观察到的优势 | 主要限制 |
| --- | --- | --- |
| 配置 | 顶层 `ConfigModel` 字段由 example YAML 提供默认值；schema 测试减少顶层字段漂移。 | 嵌套 `TeamSetting` 仍有硬编码默认值；迁移路径多且依赖版本条件，schema 测试不等于迁移保真测试。 |
| 资源同步 | 服务与 Qt worker 分开；有清单、计划、整包大小与哈希校验、逐文件复制前哈希校验、进度及失败信号。 | 删除动作具有实际文件副作用；逐文件长度与复制后完整性未验证，需保护路径边界并测试中断后的状态一致性。 |
| 自动化 | `Automation` 封装输入和截图/识别入口，允许后端实现独立演进。 | 多个输入实现与任务逻辑并存，接口契约容易漂移；截图 `None` 可能被内层循环反复等待。 |
| Mirror | 主流程、路线、商店职责有模块划分。 | 任务模块较大；无限循环和固定等待需要逐处审查局部超时、取消与失败结果。 |
| 验证 | 存在可重复 pytest 和 CI 配置。 | 自动化测试数量有限，不能支撑整条游戏操作流或打包发布的稳定性结论。 |

## 与 LALC 的比较和适配

- AALC 与目标维护 Fork 同为 Python/PySide6/Windows 桌面程序，配置、截图、输入、Mirror 和资源同步的对应关系直接，适合优先复用其边界设计和测试思路。
- LALC 的 Flutter + Python/WebSocket 架构把界面、请求生命周期和任务图拆得更明显；它的请求 ID、心跳与任务图表达值得参考，跨进程和新 UI 栈的运行成本不适用于当前桌面结构。
- 两个参考仓库都展示了识别与任务决策分层的方向；当前 Fork 已有自己的 `Automation` 与 PySide 任务边界，应补契约和离线状态测试，再决定是否抽取更小接口。
- 两边都存在循环等待或取消/更新边界需要复核的实现，AALC 的校验清单和 LALC 的任务图都不能替代当前 Fork 的回归验证。

## 对当前维护 Fork 的借鉴建议

| 思路 | 结论 | 适配方式 |
| --- | --- | --- |
| 顶层 `ConfigModel` 从 example YAML 读取默认值 | 适合沿用 | 不推断嵌套 `TeamSetting` 同样无硬编码默认值；增加字段时同时更新 schema 对齐和配置迁移测试。 |
| 清单转为显式同步计划，并记录每项增删改 | 适合沿用 | 把所有删除候选限制在明确的受管目录，并测试中断、重试和再次同步的结果。 |
| 整包大小/哈希校验与复制前逐文件哈希校验 | 适合沿用 | 当前单文件路径未检查声明长度或复制后目标；本项目应为目标文件增加包含关系、长度与哈希验证。 |
| 网络/文件服务与 UI 线程分离，以信号回报进度和失败 | 适合沿用 | 保持现有 PySide 边界，增加取消、停止和部分失败后的恢复测试。 |
| 大型 Mirror 控制流里的循环和坐标决策 | 只复用业务语义，不照搬实现 | 每个状态等待都需明确超时、最大尝试数、用户停止检查和失败出口；坐标定位需有 fixture 覆盖。 |
| 以随机输入、行为伪装规避安全审计 | 不采用 | 与本项目的安全边界冲突；只处理合法输入路径上的稳定性、可诊断性和可停止性。 |

## 待继续核验

- 资源清单路径验证和 `assets_dir` 的真实约束需与发布端清单生成器、资源更新入口一并复核。
- updater 的下载、替换、回滚与权限边界尚未完成端到端分析。
- pytest 未在此参考检出运行，CI 配置也未执行；本报告不包含通过率或打包成功率结论。
