### 项目代码审计与分析报告

根据您的要求，我已对当前项目 [AhabAssistantLimbusCompany](https://github.com/KIYI671/AhabAssistantLimbusCompany) 的代码进行了初步分析。以下是针对所提及问题的审计结果报告：

#### 1. 严重BUG 1：“合成：四级优先” 策略失效
**问题定位**：主要集中在 `tasks/mirror/in_shop.py` 文件中的 `Shop` 类。
- 在初始设置商店策略时，`team_setting.shop_strategy == 2` 代表“激进合成（四级优先）”，此时开启 `fuse_aggressive_switch`。
- 但是在 `fuse_gift` 函数（约922行起）中，处理逻辑如下：
  ```python
  def fuse_gift(self):
      # 激进合成
      if self.fuse_aggressive_switch and not self.only_system_fuse:
          if self.enter_fuse() is False:
              return False
          self.fuse_useless_gifts_aggressive()
          auto.mouse_click_blank(times=3)
      # ...
      # 再次激进合成
      if self.fuse_aggressive_switch and self.fuse_IV is not True and not self.only_system_fuse:
          if self.enter_fuse() is False:
              return False
          self.fuse_useless_gifts_aggressive()
          auto.mouse_click_blank(times=3)
  ```
- 问题在于 `enter_fuse()` 内部调用 `fuse_gift_assets.png` 等前置点击，而实际合成逻辑在 `fuse_useless_gifts_aggressive()` 和 `fuse_useless_gifts()` 中。但在这些合成函数里，它们对图像目标的匹配逻辑存在错误。它们使用 `auto.find_element("mirror/shop/fuse_label.png", find_type="image_with_multiple_targets")` 来找到可合成饰品，并依赖坐标偏移行列（`first_gift[0] + 190 * (i % 5) * scale` 等）。
- 另外，“合成四级优先”在合成达到四级后需要退出状态，通过 `self.after_fuse_IV()` 调整 `fuse_aggressive_switch = False`。但在一些逻辑分支里（例如合成失败、饰品不足三个、遇到需要保护的饰品没处理好），程序会跳出或卡在识别上，导致无法正常合成，或者执行无效点击。

#### 2. 严重BUG 2：“观测EGO饰品” 无法准确选取想要的饰品
**问题定位**：集中在 `tasks/mirror/mirror.py` 中的 `select_observe_ego_gift` 函数。
- 观测饰品列表选择时，它首先定位基准点 `benchmark_point`（如“燃烧”或“流血”体系标签图标），以此来推断饰品框的坐标区域。
- 然而，它在定位具体的饰品时，通过遍历配置文件中用户选中的饰品 `self.observe_ego_gift_selected`，利用解析文件名前缀获取体系名（如 `bleed_3_3_7.png` -> `bleed`），然后计算相对于基准点的行和列进行硬编码坐标计算。
- 由于不同屏幕分辨率适配、以及有时新版本游戏 UI 微调导致行距或列距有偏差，硬编码距离 `165 * my_scale` 等会造成点击偏移，导致完全点错或点不到想要的饰品。

#### 3. 中等问题 1：图像识别效率低下，鼠标点击延迟过大
**问题定位**：集中在 `module/automation/automation.py` 及 `input.py`，`background_input.py`。
- 自动化类中的 `mouse_action_with_pos` 引入了 `cfg.mouse_action_interval`（默认可能很高）或每次执行强制 `sleep`。
- 在每次操作后或查找元素时，都强制执行了 `self.wait_pause()` 以及很多随意的 `sleep(1)` 或 `sleep(2)`。
- `auto.find_element` 重试逻辑在屏幕内容变化不快时会无脑地调用 `take_screenshot()` 和 `match_template`，却没有有效的节流机制。
- 点击操作比如 `mouse_click` 里的模拟按键后调用了各种显式的短时或中时延宕。
- 引入更高效的方案如更优秀的 OCR（如直接缓存常用文字模板位置）、优化 ORB 特征匹配参数或减少多余截屏等都可以改善此问题。

#### 4. 中等问题 2：镜牢“镜像迷宫”选路过程效率待优化
**问题定位**：集中在 `tasks/mirror/search_road.py` 和 `tasks/mirror/mirror.py`。
- `search_road` 和 `search_road_default_distance` 大量使用了图像搜索（`auto.find_feature_element`）在预设坐标偏移的位置查找 `shop.png`, `event.png` 等。
- 每检查一条路线就会重新截图，再调用 ORB 特征匹配 `find_feature_element`，这是非常耗时的运算，尤其在一个包含很多节点的树状地图上。
- 它的选路策略是先查看当前巴士位置，基于巴士的坐标推算上、中、下三条路线节点的坐标，再挨个提取小方框截图，跑一遍图像识别。这既容易因坐标飘移找错，又极其耗时。

---
**后续计划**：
我将依据分析结果分步修改这些问题，从逻辑修正到延迟和寻路算法的性能优化。

#### 5. 底层框架与架构级优化分析（对标行业最佳实践）
结合目前游戏自动化领域的行业标准（如 MAA, Alas 等），当前项目的底层框架仍存在极大的重构优化空间，并非最优解。
1. **逻辑控制与稳定性**：
   - 现状：采用“命令式线性脚本”风格，严重依赖硬编码的 `sleep()` 盲等和 `while True` 死循环进行状态控制。遇到游戏卡顿或弹窗容易抛出异常或死循环。
   - 最优解：引入 **有限状态机 (FSM)** 设计，定义每个界面的独有状态与转移策略。实现 `wait_until_appear` 等动态等待机制，不仅能将延迟压缩到毫秒级，还能大幅提升异常恢复能力。
2. **图像识别效率**：
   - 现状：滥用了不必要的全图 `take_screenshot`，并且在寻路等功能中过度使用了极其耗时且消耗 CPU 的 ORB 特征匹配 (`feature_matching`)。
   - 最优解：限制扫描的**感兴趣区域 (ROI)**。使用低开销的固定模板匹配（`TM_CCOEFF_NORMED`），并在关键节点使用像素采样侦测变化，从而避免重复的复杂识别。
3. **反检测与安全规避（重要）**：
   - 现状：鼠标点击逻辑（例如 `pyautogui.click()` 和 `mouse_click_blank`）存在极高的机械重复性，坐标偏移 `random.randint(-10, 10)` 的随机散布也相对简陋。对于具有自动化行为分析和检测机制的游戏（如《Limbus Company》），长期的均速直线拖拽、固定频率点击极易触发封号机制。
   - 最优解：所有模拟点击必须加入**非线性的人性化轨迹（如贝塞尔曲线拖动）**；点击间隔时间引入**泊松分布或高斯分布随机数**，模拟人类玩家的反应延迟（不能仅为了追求极速而压缩至 0 延迟）；使用底层随机化的按下-弹起随机时间戳，最大程度在系统层面规避检测。

