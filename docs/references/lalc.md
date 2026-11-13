# LALC 本地参考实现分析

## 检出身份与边界

- 仓库：`E:\PUBLIC\Project\AALC\Source Code\LixAssistantLimbusCompany`
- 分支：`master`，与 `origin/master` 对齐；审阅时工作区干净。
- HEAD：`431b432e22f0b0da08b95d7c478fa213be20b3e8`
- 标签：`v5.0.0`
- 许可证：GNU AGPL v3，见 `LICENSE`。
- 审阅类型：静态代码与仓库文件审阅；未在此检出运行测试、构建程序或连接真实游戏。结论仅对应上述 SHA。
- 测试检索：未发现后端 pytest/unittest 测试文件或 Flutter `*_test.dart` 测试。仓库中的手工测试辅助函数不等价于可重复的自动化测试。

## 架构与实现

### 前端、后端与命令生命周期

前端使用 Flutter/Dart，后端使用 Python。两者通过本机 WebSocket 交换配置、业务命令和响应：`lalc_backend/server.py:1438-1523`。服务端优先尝试 `localhost:8765`，绑定失败后再尝试 `8766`；收到 JSON 后区分心跳、配置和 request 命令，并用请求 ID 回传结果。

前端 `WebSocketManager` 为普通命令生成 UUID 请求 ID、登记 pending callback，在收到响应后执行并移除 callback：`lalc_frontend/lib/managers/websocket_manager.dart:826-894,260-296`。前端每秒发送心跳，并在发送时取消、重建 20 秒计时器：`lalc_frontend/lib/managers/websocket_manager.dart:634-646`。因此，只要心跳持续发送，未收到 ACK 本身不会让该计时器到期。计时器回调只把前端任务状态改为停止并更新连接状态；未向后端发送停止命令：`lalc_frontend/lib/managers/websocket_manager.dart:646-663`、`lalc_frontend/lib/managers/task_status_manager.dart:40-43`。

`lalc_frontend/lib/managers/command_gateway.dart:34-92` 在发命令前检查连接、运行状态、队伍配置和偏好 EGO 类型。这将一部分配置错误挡在任务启动之前。后端 `lalc_backend/server.py:573-1423` 仍通过较大的手写命令分支完成配置转换与业务路由，未在本次静态检查中发现覆盖所有请求形状的统一 schema 模型。

### 工作流与识别

`lalc_backend/workflow/task_node.py:21-49,120-174` 将任务表示为节点：节点有动作名、识别类型、参数、后继和中断路径；可选择 direct、template、color-template 或 feature 识别，也可配置反向匹配。`normal_node_get_next()` 使用同一张截图依次检查后继，再检查中断节点：`lalc_backend/workflow/task_node.py:120-135`。`doc/task_pipeline.md` 描述了 JSON 驱动的任务节点配置。

识别实现经由 `lalc_backend/recognize/img_recognizer.py` 暴露模板、颜色、特征和文字识别接口，并支持区域 mask 与匹配阈值：`:38-64,116-157,185-202`。工作流因此无需直接依赖各识别算法细节。

`lalc_backend/workflow/async_task_pipeline.py:238-297` 以 asyncio 管理任务栈，但每个动作同步运行于 `run_in_executor()`：`lalc_backend/workflow/async_task_pipeline.py:250-271`。外部 `stop(force_cancel=True)` 会取消 asyncio worker：`lalc_backend/workflow/async_task_pipeline.py:417-442`；这不证明 executor 中已经开始运行的同步函数能够立即停止，需由动作本身提供协作停止检查或安全退出边界。

更新管理器的流式下载在 asyncio 函数中同步迭代 `response.iter_content()`，每次取得数据块后才让出事件循环：`lalc_backend/utils/update_manager.py:39-44`。网络读取等待期间，其他协程的响应和取消处理也会延迟；这比单纯的 executor 取消边界更广。

### 等待、更新与输入副作用

部分识别等待没有本地截止时间，例如 `lalc_backend/task_action/base.py:92-101` 的 `wait_disappear` 和 `lalc_backend/task_action/mirror.py:21-30` 的失败画面等待。即使流水线支持暂停/停止，也需要逐个验证同步动作是否会返回控制权。

`lalc_backend/input/input_handler.py:54-122` 在若干前台与后台点击/拖动期间调用系统级 `BlockInput(True)`，并在 `finally` 中恢复。`finally` 覆盖普通 Python 异常路径，但系统范围输入屏蔽仍具有明显副作用，不能视为只影响游戏窗口；本次没有验证进程强制退出或系统调用失败时的恢复行为。

`lalc_backend/utils/update_manager.py:25-59,90-137` 提供下载进度和协程取消检查；但 API 查询在 executor 内执行同步 `requests.get()`，其中一处未设置超时，另一次资源请求设置了 30 秒超时：`lalc_backend/utils/update_manager.py:90-128`。流式 `iter_content()` 仍在 asyncio 协程中同步读取：`lalc_backend/utils/update_manager.py:39-44`。目标路径中同名下载文件会在查询 release 前删除：`lalc_backend/utils/update_manager.py:84-88`。

`update_to.bat:1-39` 要求非空源和目标参数并检查源目录存在；之后会遍历并删除目标目录内容再 `robocopy`：`:53-105`。脚本没有在已检查片段中证明目标目录是预期安装目录，因此路径误传可能造成目标目录数据丢失。

## 工程质量判断

| 领域 | 观察到的优势 | 主要限制 |
| --- | --- | --- |
| 前后端通信 | 请求 ID 和 pending callbacks 有明确的响应关联。 | 心跳计时器每秒被重置；不能据此认定无响应能触发失联检测或停止后端任务。命令消息仍缺少统一 schema。 |
| 工作流 | 节点图把识别、分支、中断和动作注册分离，可用配置表达流程；任务注册器已检查 next/interrupt 引用。 | 任意 `**kwargs` 和同步动作扩大配置错误与取消边界；动作参数和识别类型仍需完整 schema 校验。 |
| 识别 | 模板、颜色、特征和 OCR 收敛到一个 handler，支持 mask 与阈值。 | 算法接口统一不代表失败契约统一；调用方仍需处理空结果、异常和耗时。 |
| 更新 | 有进度回调与下载阶段取消点。 | executor 中的同步请求和协程中的同步流读取都不能因 wrapper coroutine 被取消就被认为已停止；更新脚本会清理传入的目标目录。 |
| 验证 | 工作流文档存在，`pubspec.yaml` 声明 `flutter_test`，GitHub workflow 包括发布和维护任务。 | 本次文件搜索未发现后端自动化测试或 Flutter `test/` 测试源码；依赖声明和发布 workflow 不等于行为回归证据。 |

## 对当前维护 Fork 的借鉴建议

| 思路 | 结论 | 适配方式 |
| --- | --- | --- |
| 任务启动前检查队伍、连接和运行状态 | 适合沿用 | 在 PySide 任务启动入口复用当前配置模型做可见的预检，并测试每个拒绝原因。 |
| 识别操作通过窄接口暴露模板、OCR、mask 和阈值 | 适合沿用 | 延续现有 `Automation` / OCR 边界，补充明确的结果类型与失败原因；无需引入 Flutter/WebSocket。 |
| 节点图表达分支、识别、打断和计数 | 可借鉴建模方法 | 仓库已有 next/interrupt 节点引用校验：`lalc_backend/workflow/task_registry.py:172-208,219-236`；若借鉴此模型，补充动作参数和识别类型等完整 schema 校验。保留 Python 任务 API，禁止无验证的大规模框架移植。 |
| 前端请求 ID 与 pending callback 的生命周期 | 只在跨进程 UI/API 场景适用 | 当前应用为本机 PySide 桌面程序，通信边界不同；借用“关联请求与响应”的原则即可，超时与后端停止语义需分别设计。 |
| 未限时的消失等待、长时间同步动作和整目录更新清理 | 不采用原样实现 | 为识别等待设超时和终态，为同步动作加入协作取消，为更新路径增加明确的根目录校验和恢复流程。 |
| 全局输入屏蔽作为普通输入手段 | 不采用为默认方案 | 其副作用超出目标窗口；任何现有使用必须保证作用域短、异常时恢复并由测试覆盖。 |

## 参考项目比较结论

- 两个参考仓库都采用 GNU AGPL v3；版本身份和许可证来自本地检出文件。代码借用仍需保持来源标记、许可证义务和具体文件的许可证核对。
- AALC 的模块结构、PySide6、Python 配置模型、资源清单和 Qt worker 更贴近当前维护 Fork；优先比较同职责模块，避免把上游差异误作可直接替换的实现。
- LALC 的配置驱动任务图、识别接口和请求/响应生命周期对扩展工作流有启发；它的 Flutter + WebSocket + executor 架构引入明显的依赖和运维成本，不适合为局部稳定性问题整体迁移。
- 两个仓库都能提供可借鉴设计，但都存在需要进一步测试的等待、取消或更新边界；参考实现不能替代当前 Fork 的离线回归测试。

## 待继续核验

- 服务端命令分支与所有配置载荷的有效 schema 范围尚未逐条建模。
- 下载取消期间 executor 中同步请求的结束时机和响应对象清理尚未通过运行测试确认。
- 未运行 Flutter、后端或打包验证；本报告不包含运行成功率、当前远端发布状态或实际更新安全结论。

本检出在后续文档调查中再次确认仍为上述 SHA；任务图和跨进程架构的适用条件见[目标架构与优化](../architecture/target-and-optimization.md)。后续调查未运行参考项目。
