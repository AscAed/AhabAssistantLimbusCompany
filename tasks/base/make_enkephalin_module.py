import time

from module.automation import auto
from module.config import cfg
from module.decorator.decorator import begin_and_finish_time_log
from module.logger import log
from module.my_error.my_error import userStopError

ENKEPHALIN_PREPARATION_TIMEOUT_SECONDS = 60
GRANDET_TIMING_TIMEOUT_SECONDS = 90
MAX_ENKEPHALIN_POPUP_RECOVERIES = 3
MAX_LUNACY_SCREENSHOT_ATTEMPTS = 5


class EnkephalinPreparationError(RuntimeError):
    pass


class EnkephalinPreparationTimeout(TimeoutError):
    pass


def _check_stop_requested() -> None:
    auto.sleep_with_stop_check(0)


def _wait_for_grandet_timing(already_qualified: bool) -> bool:
    start_time = time.monotonic()
    while True:
        _check_stop_requested()
        if time.monotonic() - start_time >= GRANDET_TIMING_TIMEOUT_SECONDS:
            raise EnkephalinPreparationTimeout(
                "葛朗台模式等待体力计时器超时"
                f"（{GRANDET_TIMING_TIMEOUT_SECONDS}秒）"
            )
        timing_ready = get_the_timing()
        if timing_ready is None:
            raise EnkephalinPreparationError(
                "葛朗台模式无法识别体力回复计时器，已停止狂气消耗"
            )
        if timing_ready is True or already_qualified:
            return True
        auto.sleep_with_stop_check(2)


def get_the_timing(return_time=False):
    if module_position := auto.find_element(
        "enkephalin/lunacy_assets.png", take_screenshot=True
    ):
        my_scale = cfg.set_win_size / 1440
        bbox = (
            module_position[0] - 200 * my_scale,
            module_position[1] + 150 * my_scale,
            module_position[0] + 600 * my_scale,
            module_position[1] + 220 * my_scale,
        )
        ocr_result = auto.find_text_element(None, my_crop=bbox, only_text=True)
        if ocr_result is None:
            return None
        try:
            s = "".join(str(ocr) for ocr in ocr_result)
            if ":" not in s:
                return None
            parts = s.split(":")
            minute = int(parts[0][-2:])
            seconds = int(parts[1][:2])
            if return_time:
                return minute * 60 + seconds
            if minute >= 5 and seconds >= 20:
                log.debug(
                    f"生成下一点体力的时间为{minute}分{seconds}秒，符合葛朗台模式操作"
                )
                return True
            return False
        except Exception:
            return None
    return None


def get_current_enkephalin():
    import cv2
    import numpy as np

    from module.ocr import ocr
    from module.ocr.ocr import OCRExecutionError
    from utils.image_utils import ImageUtils

    enkephalin_bbox = ImageUtils.get_bbox(
        ImageUtils.load_image("enkephalin/enkephalin_now_bbox.png")
    )
    screenshot_available = False
    for _ in range(5):
        if auto.take_screenshot() is None:
            continue
        screenshot_available = True
        try:
            sc = ImageUtils.crop(np.array(auto.screenshot), enkephalin_bbox)
            _, binary_image = cv2.threshold(sc, 110, 255, cv2.THRESH_BINARY)
            result = ocr.run(binary_image)
            ocr_result = [result.txts[i] for i in range(len(result.txts))]
            ocr_result = "".join(ocr_result)
            ocr_result = ocr_result.lower()
            if "/" in ocr_result:
                ocr_result = ocr_result.split("/")
                current_enkephalin = int(ocr_result[0])
                return current_enkephalin
        except (userStopError, OCRExecutionError):
            raise
        except Exception:
            continue
    if not screenshot_available:
        return None
    try:
        sc = ImageUtils.crop(np.array(auto.screenshot), enkephalin_bbox)
        _, binary_image = cv2.threshold(sc, 150, 255, cv2.THRESH_BINARY)
        result = ocr.run(binary_image)
        ocr_result = [result.txts[i] for i in range(len(result.txts))]
        ocr_result = "".join(ocr_result)
        current_enkephalin = int(ocr_result[0])
        return current_enkephalin
    except (userStopError, OCRExecutionError):
        raise
    except Exception:
        pass
    return None


@begin_and_finish_time_log(task_name="体力换饼", calculate_time=False)
def make_enkephalin_module(cancel=True, skip=True, *, task_name: str = "体力换饼"):
    """体力换饼的模块
    Args:
        cancel (bool): 是否点击取消按钮 (即关闭换体界面)
        skip (bool): 是否遵循设置跳过换体 (优先于cfg.skip_enkephalin)
    """
    if skip and cfg.skip_enkephalin:
        return

    import time

    start_time = time.time()
    last_log_time = None
    first_popup_warning = True
    use_lunacy_threshold = 0.8
    all_in_threshold = 0.8
    popup_marker_threshold = 0.7
    open_panel_click_cooldown = 0.5
    last_open_panel_click_time = 0.0
    popup_recovery_count = 0

    def recover_popup():
        nonlocal popup_recovery_count
        if popup_recovery_count >= MAX_ENKEPHALIN_POPUP_RECOVERIES:
            raise EnkephalinPreparationError(
                f"{task_name}弹窗恢复次数超限"
                f"（{MAX_ENKEPHALIN_POPUP_RECOVERIES}次）"
            )
        popup_recovery_count += 1
        from tasks.base.back_init_menu import back_init_menu

        if back_init_menu(allow_restart=False) is False:
            raise EnkephalinPreparationError(f"{task_name}弹窗恢复失败")

    while True:
        _check_stop_requested()
        now_time = time.time()
        if auto.get_restore_time() is not None:
            start_time = max(start_time, auto.get_restore_time())
        if 60 > now_time - start_time > 20 and int(now_time - start_time) % 10 == 0:
            if last_log_time is None or now_time - last_log_time > 5:
                msg = f"已尝试{task_name}超过{int(now_time - start_time)}秒，如果非电脑硬件配置不足，请确认是否执行了正确的语言配置"
                log.warning(msg)
                last_log_time = now_time
        if now_time - start_time >= ENKEPHALIN_PREPARATION_TIMEOUT_SECONDS:
            from app import mediator

            if first_popup_warning and (
                last_log_time is None or now_time - last_log_time > 5
            ):
                # only do it once
                first_popup_warning = False
                log.warning(
                    f"已尝试{task_name}超过1分钟，脚本将停止运行，请先检查语言配置，或检查电脑配置是否支持"
                )
                mediator.link_start.emit()
                message = (
                    f"脚本卡死在{task_name}，请检查语言配置，或检查电脑配置是否支持"
                )
                mediator.warning.emit(message)
            raise EnkephalinPreparationTimeout(
                f"{task_name}资源面板确认超时"
                f"（{ENKEPHALIN_PREPARATION_TIMEOUT_SECONDS}秒）"
            )
        # 自动截图
        if auto.take_screenshot() is None:
            continue
        _check_stop_requested()
        auto.mouse_to_blank()
        if auto.find_element(
            "base/update_close_assets.png", model="clam"
        ) and auto.find_element("home/drive_assets.png", model="normal"):
            _check_stop_requested()
            auto.click_element("base/update_close_assets.png")
            recover_popup()
            continue
        if auto.find_element(
            "base/renew_confirm_assets.png", model="clam"
        ) and auto.find_element("home/drive_assets.png", model="normal"):
            _check_stop_requested()
            auto.click_element("base/renew_confirm_assets.png")
            recover_popup()
            continue
        panel_visible = bool(
            auto.find_element(
                "enkephalin/use_lunacy_assets.png", threshold=use_lunacy_threshold
            )
            or auto.find_element(
                "enkephalin/enkephalin_cancel_assets.png",
                threshold=popup_marker_threshold,
            )
            or auto.find_element(
                "enkephalin/all_in_assets.png", threshold=all_in_threshold
            )
        )
        if not panel_visible:
            _check_stop_requested()
            if (
                now_time - last_open_panel_click_time >= open_panel_click_cooldown
                and auto.click_element(
                    "home/enkephalin_box_assets.png",
                    threshold=0.75,
                    offset=False,
                )
            ):
                last_open_panel_click_time = now_time
                auto.sleep_with_stop_check(0.5)
            continue
        _check_stop_requested()
        if auto.click_element(
            "enkephalin/all_in_assets.png",
            threshold=all_in_threshold,
        ):
            auto.sleep_with_stop_check(0.2)
            if auto.take_screenshot() is None:
                continue
            _check_stop_requested()
            auto.click_element("enkephalin/enkephalin_confirm_assets.png")
            if cancel:
                _check_stop_requested()
                auto.click_element("enkephalin/enkephalin_cancel_assets.png")
            return True
        auto.sleep_with_stop_check(0.2)
        continue


@begin_and_finish_time_log(task_name="狂气换体", calculate_time=False)
def lunacy_to_enkephalin(times=0):
    _check_stop_requested()
    make_enkephalin_module(cancel=False, skip=False, task_name="狂气换体")
    _check_stop_requested()
    auto.click_element("enkephalin/use_lunacy_assets.png")
    auto.sleep_with_stop_check(0.5)
    Grandet = False
    remaining_times = times
    while remaining_times > 0:
        _check_stop_requested()
        auto.mouse_to_blank(move_back=False)
        for attempt in range(MAX_LUNACY_SCREENSHOT_ATTEMPTS):
            _check_stop_requested()
            if auto.take_screenshot() is not None:
                break
            if attempt + 1 < MAX_LUNACY_SCREENSHOT_ATTEMPTS:
                auto.sleep_with_stop_check(0.1)
        else:
            raise EnkephalinPreparationError(
                "狂气换体连续截图失败，已停止后续操作"
            )
        _check_stop_requested()
        if auto.find_element("enkephalin/lunacy_spend_26_assets.png"):
            # 葛朗台模式
            if cfg.Dr_Grandet_mode:
                Grandet = _wait_for_grandet_timing(Grandet)
            _check_stop_requested()
            auto.click_element("enkephalin/enkephalin_confirm_assets.png")
            auto.sleep_with_stop_check(1)
            remaining_times -= 1
            continue
        if remaining_times >= 2 and auto.find_element(
            "enkephalin/lunacy_spend_52_assets.png"
        ):
            if cfg.Dr_Grandet_mode:
                Grandet = _wait_for_grandet_timing(Grandet)
            _check_stop_requested()
            auto.click_element("enkephalin/enkephalin_confirm_assets.png")
            auto.sleep_with_stop_check(1)
            remaining_times -= 2
            continue
        if remaining_times >= 3 and auto.find_element(
            "enkephalin/lunacy_spend_78_assets.png"
        ):
            if cfg.Dr_Grandet_mode:
                Grandet = _wait_for_grandet_timing(Grandet)
            _check_stop_requested()
            auto.click_element("enkephalin/enkephalin_confirm_assets.png")
            auto.sleep_with_stop_check(1)
            remaining_times -= 3
            continue
        break
    _check_stop_requested()
    auto.click_element("enkephalin/enkephalin_cancel_assets.png")
    _check_stop_requested()
    make_enkephalin_module(skip=False)
