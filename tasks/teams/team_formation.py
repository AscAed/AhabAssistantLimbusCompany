from time import sleep

from PIL import ImageChops

from module.automation import auto
from module.config import cfg
from module.decorator.decorator import begin_and_finish_time_log
from module.logger import log
from module.my_error.my_error import userStopError

MAX_SCREENSHOT_ATTEMPTS = 3
MAX_CLEAN_TEAM_ATTEMPTS = 30


def _capture_screenshot_with_retries():
    last_error = None
    for attempt in range(1, MAX_SCREENSHOT_ATTEMPTS + 1):
        try:
            screenshot = auto.take_screenshot()
        except userStopError:
            raise
        except Exception as exc:
            last_error = exc
            log.warning(
                "队伍界面截图失败（%s/%s）: %s",
                attempt,
                MAX_SCREENSHOT_ATTEMPTS,
                exc,
            )
            continue
        if screenshot is not None:
            return screenshot

    if last_error is not None:
        log.error("队伍界面截图连续失败，已停止")
    return None


def _scroll_pane_changed(before, after, region) -> bool:
    if before.size != after.size:
        return False

    width, height = before.size
    left, top, right, bottom = (int(value) for value in region)
    left = max(0, min(width, left))
    top = max(0, min(height, top))
    right = max(0, min(width, right))
    bottom = max(0, min(height, bottom))
    if right <= left or bottom <= top:
        return False

    before_pane = before.convert("L").crop((left, top, right, bottom))
    after_pane = after.convert("L").crop((left, top, right, bottom))
    difference = ImageChops.difference(before_pane, after_pane).point(
        lambda pixel: 255 if pixel > 16 else 0
    )
    changed_pixels = sum(difference.histogram()[1:])
    minimum_changed_pixels = max(32, ((right - left) * (bottom - top)) // 500)
    return changed_pixels >= minimum_changed_pixels


def _scroll_pane_region(first_position, scale, screenshot):
    width, height = screenshot.size
    x, y = first_position
    return (
        max(0, int(x - 60 * scale)),
        max(0, int(y - 100 * scale)),
        min(width, int(x + 800 * scale)),
        min(height, int(y + 700 * scale)),
    )


def _first_team_row_visible(position, scale) -> bool:
    first_row = auto.find_language_text(
        "编队#1",
        ["TEAMS #1", "TEAMS#1", "TFAMS#1"],
        my_crop=(0, 0, position[0] + 130 * scale, position[1] + 600 * scale),
    )
    if hasattr(first_row, "position"):
        first_row = first_row.position
    if not first_row:
        return False

    expected_y = position[1] + 220 * scale
    row_y = first_row[1]
    return expected_y - 50 * scale <= row_y <= expected_y + 50 * scale


# 清队
def clean_team():
    scale = cfg.set_win_size / 1440
    for _ in range(MAX_CLEAN_TEAM_ATTEMPTS):
        # 自动截图
        if _capture_screenshot_with_retries() is None:
            log.error("清理队伍时无法获取截图，已停止")
            return False
        if auto.click_element("teams/clear_selection_confirm_assets.png"):
            return True
        if (
            identify_position := auto.find_element("teams/identify_assets.png")
        ) and auto.mouse_action_with_pos(
            [identify_position[0], identify_position[1] + 600 * scale]
        ):
            sleep(0.5)
            if _capture_screenshot_with_retries() is None:
                log.error("清理队伍后无法验证截图，已停止")
                return False
            if auto.find_element("teams/clear_selection_confirm_assets.png") is None:
                return True

    log.error("清理队伍达到最大尝试次数，已停止")
    return False


# 编队
@begin_and_finish_time_log(task_name="罪人编队")
def team_formation(sinner_team):
    if not any(sinner_team):
        log.error("队伍中未选择罪人，已停止编队")
        return False
    scale = cfg.set_win_size / 1440

    if not clean_team():
        log.error("清理现有队伍失败，已停止编队")
        return False
    if _capture_screenshot_with_retries() is None:
        log.error("编队前无法获取截图，已停止")
        return False
    if reset_team := auto.find_element("teams/identify_assets.png"):
        first_sinner = [reset_team[0] - 1800 * scale, reset_team[1] + 130 * scale]
    else:
        log.error("无法找到罪人编队的起始位置")
        return False
    sleep(0.5)

    for i in range(1, 13):
        if i in sinner_team:
            sinner = sinner_team.index(i)
        else:
            continue
        if sinner <= 5:
            auto.mouse_click(first_sinner[0] + 270 * sinner * scale, first_sinner[1])
        else:
            auto.mouse_click(
                first_sinner[0] + 270 * (sinner - 6) * scale,
                first_sinner[1] + 500 * scale,
            )
        sleep(cfg.mouse_action_interval)
    return True


@begin_and_finish_time_log(task_name="寻找队伍")
# 找队
def select_battle_team(num):
    scale = cfg.set_win_size / 1440
    my_position = [0, 150 * scale]
    if _capture_screenshot_with_retries() is None:
        log.error("寻找队伍时无法获取截图，已停止")
        return False
    if auto.find_element(
        "home/first_prompt_assets.png", model="clam"
    ) and auto.find_element("home/back_assets.png", model="normal"):
        auto.click_element("home/back_assets.png")
    if identify_position := auto.find_element(
        "teams/identify_assets.png", take_screenshot=True
    ):
        position = [
            identify_position[0] - 2150 * scale,
            identify_position[1] + 215 * scale,
        ]
        auto.mouse_click(1, 1)
        my_position[0] += position[0]
        my_position[1] += position[1]
        auto.mouse_click(my_position[0], my_position[1])
        sleep(0.5)

        def report_background_input_result(success: bool) -> None:
            if hasattr(auto, "report_background_input_result"):
                auto.report_background_input_result(success)

        def scroll_once(direction, x, y, count=1):
            try:
                # Use batch_mouse_scroll if available (WindowMoveInput mode)
                if hasattr(auto, 'batch_mouse_scroll') and auto.batch_mouse_scroll is not None:
                    return auto.batch_mouse_scroll(direction, count, x, y)
                # Fallback to single scroll for other modes
                elif hasattr(auto, 'mouse_scroll') and auto.mouse_scroll is not None:
                    for _ in range(count):
                        if not auto.mouse_scroll(direction, x, y):
                            return False
                    return True
                return False
            except Exception as exc:
                log.warning("滚轮投递失败，将尝试窗口拖拽兜底: %s", exc)
                return False

        def scroll_with_verification(
            first_pos,
            *,
            direction,
            count,
            drag_start_y,
            drag_distance,
            drag_time,
            allow_top_row=False,
            top_retry=0,
        ):
            before = _capture_screenshot_with_retries()
            if before is None:
                log.error("滚动队伍列表前无法获取截图，已停止")
                return False

            scroll_success = scroll_once(
                direction,
                int(first_pos[0]),
                int(first_pos[1] + 150 * scale),
                count=count,
            )
            after_scroll = _capture_screenshot_with_retries()
            if after_scroll is None:
                log.error("滚动队伍列表后无法获取截图，已停止")
                return False

            pane_region = _scroll_pane_region(first_pos, scale, before)
            if scroll_success and _scroll_pane_changed(before, after_scroll, pane_region):
                if not allow_top_row or _first_team_row_visible(position, scale):
                    report_background_input_result(True)
                    return True
            if allow_top_row and _first_team_row_visible(position, scale):
                return True

            report_background_input_result(False)
            try:
                auto.mouse_drag(
                    first_pos[0],
                    drag_start_y,
                    dy=drag_distance,
                    drag_time=drag_time,
                )
                sleep(0.2)
            except Exception as exc:
                log.error("队伍列表窗口拖拽兜底失败: %s", exc)
                return False

            after_drag = _capture_screenshot_with_retries()
            if after_drag is None:
                log.error("拖拽队伍列表后无法获取截图，已停止")
                return False
            if _scroll_pane_changed(before, after_drag, pane_region):
                if not allow_top_row or _first_team_row_visible(position, scale):
                    return True
                if top_retry >= 2:
                    return False
                log.debug("队伍列表仍未回到首行，将继续有界滚动确认")
                return scroll_with_verification(
                    first_pos,
                    direction=1,
                    count=30,
                    drag_start_y=drag_start_y,
                    drag_distance=drag_distance,
                    drag_time=drag_time,
                    allow_top_row=True,
                    top_retry=top_retry + 1,
                )
            if allow_top_row and _first_team_row_visible(position, scale):
                return True

            log.warning("队伍列表滚动后未观察到列表变化，已停止队伍选择")
            return False

        def scroll_to_top(first_pos):
            return scroll_with_verification(
                first_pos,
                direction=1,
                count=30,
                drag_start_y=first_pos[1],
                drag_distance=1000 * scale,
                drag_time=0.8,
                allow_top_row=True,
            )

        def scroll_down(first_pos, pages):
            if pages <= 0:
                return True
            return scroll_with_verification(
                first_pos,
                direction=-1,
                count=pages * 12,
                drag_start_y=first_pos[1] + 375 * scale,
                drag_distance=-375 * scale * pages,
                drag_time=0.6 * pages,
            )

        first_position = [position[0], position[1] + 70 * scale]
        if not scroll_to_top(first_position):
            return False
        sleep(0.75)

        if cfg.select_team_by_order:
            if num <= 7:
                auto.mouse_click(
                    first_position[0], first_position[1] + 75 * (num - 1) * scale
                )
            else:
                team_range = (num - 1) // 5
                team_order = (num - 1) % 5
                if not scroll_down(first_position, team_range):
                    return False
                sleep(0.75)
                if num <= 15:
                    auto.mouse_click(
                        first_position[0], first_position[1] + 75 * team_order * scale
                    )
                else:
                    auto.mouse_click(
                        first_position[0],
                        first_position[1] + 100 * scale + 75 * team_order * scale,
                    )
            log.info(f"成功找到队伍 # {num}")
            sleep(1)
            return True
        else:
            team_name_zh = "编队#" + str(num)
            team_name_en = [f"TEAMS #{num}", f"TEAMS#{num}", f"TFAMS#{num}"]
            position_bbox = (0, 0, position[0] + 130 * scale, position[1] + 600 * scale)
            for _ in range(10):
                before_drag = _capture_screenshot_with_retries()
                if before_drag is None:
                    log.error("搜索队伍名称时无法获取截图，已停止")
                    return False
                if team_position := auto.find_language_text(
                    team_name_zh, team_name_en, my_crop=position_bbox
                ):
                    auto.mouse_action_with_pos(team_position, offset=False)
                    log.info(f"成功找到队伍 # {num}")
                    sleep(1)
                    return True

                report_background_input_result(False)
                try:
                    auto.mouse_drag(
                        first_position[0],
                        first_position[1] + 375 * scale,
                        dy=-385 * scale,
                        drag_time=1.5,
                    )
                except Exception as exc:
                    log.error("搜索队伍名称时拖拽失败: %s", exc)
                    return False
                sleep(1)
                after_drag = _capture_screenshot_with_retries()
                if after_drag is None:
                    log.error("搜索队伍名称后无法获取截图，已停止")
                    return False
                pane_region = _scroll_pane_region(
                    first_position, scale, before_drag
                )
                if not _scroll_pane_changed(before_drag, after_drag, pane_region):
                    log.warning("队伍名称搜索未观察到列表变化，已停止")
                    return False

            log.info(f"找不到队伍 # {num}")
            return False
    else:
        log.error("无法找到队伍选择界面的定位锚点，已停止")
        return False


def deal_with_spills():
    import cv2
    import numpy as np

    from module.ocr import ocr
    from utils.image_utils import ImageUtils

    scale = cfg.set_win_size / 1440
    sinner_nums_bbox = ImageUtils.get_bbox(
        ImageUtils.load_image("battle/normal_to_battle_assets.png")
    )
    sinner_nums_bbox = (
        sinner_nums_bbox[0],
        sinner_nums_bbox[1] - 115 * scale,
        sinner_nums_bbox[2],
        sinner_nums_bbox[3] - 115 * scale,
    )
    sc = ImageUtils.crop(np.array(auto.screenshot), sinner_nums_bbox)
    sc = cv2.bitwise_not(sc)
    mask = cv2.inRange(sc, 220, 255)
    mask = cv2.bitwise_not(mask)
    background = np.zeros((300, 300), dtype=np.uint8)
    h, w = mask.shape[:2]
    y_off = (300 - h) // 2
    x_off = (300 - w) // 2
    background[y_off : y_off + h, x_off : x_off + w] = mask
    try:
        result = ocr.run(background)
        ocr_result = [result.txts[i] for i in range(len(result.txts))]
        ocr_result = "".join(ocr_result)
        log.debug(f"对于配队人数OCR得到：{ocr_result}")
        if "/" in ocr_result:
            result = ocr_result.split("/")
            result = [i.strip() for i in result]
            import re

            now = int(re.sub(r"\D", "", result[-2]))
            max = int(re.sub(r"\D", "", result[-1]))
            if now > max:
                all_selected = auto.find_element(
                    "teams/selected.png", find_type="image_with_multiple_targets"
                )
                kernel = np.ones((3, 3), np.uint8)
                for selected in all_selected:
                    try:
                        order_bbox = (
                            selected[0] - 40 * scale,
                            selected[1] - 120 * scale,
                            selected[0] + 40 * scale,
                            selected[1] - 30 * scale,
                        )
                        sc2 = ImageUtils.crop(np.array(auto.screenshot), order_bbox)
                        background2 = np.zeros((300, 300), dtype=np.uint8)
                        h, w = sc2.shape[:2]
                        y_off = (300 - h) // 2
                        x_off = (300 - w) // 2
                        background2[y_off : y_off + h, x_off : x_off + w] = sc2
                        result = ocr.run(background2)
                        ocr_result = [result.txts[i] for i in range(len(result.txts))]
                        ocr_result = "".join(ocr_result)
                        if ocr_result == "G":
                            ocr_result = "6"
                        if int(ocr_result) == 1:
                            # 再腐蚀 3 次
                            background2 = cv2.erode(background2, kernel, iterations=3)
                            # 再膨胀 2 次
                            background2 = cv2.dilate(background2, kernel, iterations=2)
                            result = ocr.run(background2)
                            ocr_result = [
                                result.txts[i] for i in range(len(result.txts))
                            ]
                            ocr_result = "".join(ocr_result)
                        if int(ocr_result) > max:
                            auto.mouse_click(selected[0], selected[1])
                    except Exception:
                        continue
    except Exception:
        pass


@begin_and_finish_time_log(task_name="检查队伍剩余战斗力")
def check_team():
    # 至少还有5人可以战斗
    sinner_nums = [f"{a}/{b}" for b in range(5, 10) for a in range(5, b + 1)]
    if auto.find_element(sinner_nums, find_type="text"):
        return True
    else:
        return False


@begin_and_finish_time_log(task_name="加载编队码")
def load_team_code_in_game(team_code: str) -> bool:
    """在游戏中加载编队码

    Args:
        team_code: 编队码字符串

    Returns:
        成功返回 True，失败返回 False
    """
    # 验证当前在队伍选择界面
    if not auto.find_element("mirror/road_to_mir/select_team_confirm_assets.png"):
        log.warning("未在队伍选择界面，跳过编队码加载")
        return False

    # 最多重试3次
    max_retries = 3
    for _ in range(1, max_retries + 1):
        # 截图
        if _capture_screenshot_with_retries() is None:
            log.error("加载编队码时无法获取截图，已停止")
            return False

        # 点击队伍代码按钮
        auto.click_element("teams/team_code_assets.png")
        sleep(1)

        # 查找并点击加载编队码按钮
        auto.click_element(
            "teams/load_team_code_button_assets.png", take_screenshot=True
        )
        sleep(1)

        # 查找根据取消按钮判断输入框是否出现
        if not auto.find_element(
            "teams/team_code_cancel_button_assets.png", take_screenshot=True
        ):
            # 尝试点击取消按钮返回
            auto.mouse_click_blank()
            sleep(1)
            continue

        # 使用 input_text(text) 直接输入编队码
        auto.input_text(team_code)
        sleep(0.5)  # 等待输入完成

        # 点击确认按钮，最多重试 3 次
        for _ in range(3):
            if auto.click_element(
                "teams/team_code_confirm_button_assets.png", take_screenshot=True
            ):
                sleep(1)
            else:
                break

        # 验证返回队伍选择界面
        if auto.find_element("teams/team_code_assets.png", take_screenshot=True):
            return True
        else:
            auto.click_element("teams/team_code_cancel_button_assets.png")
            sleep(1)

    auto.mouse_click(100, 100)  # 点击左上角关闭
    log.warning(f"加载编队码失败，已重试{max_retries}次: {team_code}")
    return False
