import gc
import math
import random
import time
from ast import List
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import psutil
from PIL.Image import Image

from module.my_error.my_error import withOutGameWinError
from utils.image_utils import ImageUtils
from utils.path_manager import path_manager
from utils.singletonmeta import SingletonMeta

from ..config import cfg
from ..logger import log
from ..ocr import ocr
from .input_handlers.input import AbstractInput
from .screenshot import ScreenShot


@dataclass(frozen=True)
class TextMatchResult:
    """Structured result for dict-based OCR target matches."""

    value: Any
    text: str
    position: list[float]


class Automation(metaclass=SingletonMeta):
    """自动化管理类，用于管理与游戏窗口有关的自动化操作"""

    def __init__(self, windows_title):
        self.windows_title = windows_title
        self.screenshot = None
        self.input_handler = AbstractInput()

        self.init_input()

        self.img_cache = {}
        self.location_cache = {}
        self.last_screenshot_time = 0
        self.last_click_time = 0
        self.last_memory_check_time = 0
        self.model = "clam"

    def init_input(self):
        """初始化输入处理器，将输入操作如点击、拖动等绑定至实例变量"""
        if self.input_handler:
            self.input_handler = None
        if cfg.simulator:
            if cfg.simulator_type == 0:
                from .input_handlers.simulator.mumu_control import MumuControl

                log.debug("使用MuMu模拟器输入模块")
                if MumuControl.connection_device is not None:
                    self.input_handler = MumuControl.connection_device
            else:
                from .input_handlers.simulator.simulator_control import SimulatorControl

                log.debug("使用基于PyMiniTouch的通用模拟器输入模块")
                self.input_handler = SimulatorControl.connection_device
        else:
            input_type = cfg.win_input_type
            if input_type == "background":
                from .input_handlers.input import BackgroundInput

                log.debug("使用后台点击模块")
                self.input_handler = BackgroundInput()
            elif input_type == "foreground":
                from .input_handlers.input import Input

                log.debug("使用前台点击模块")
                self.input_handler = Input()
            elif input_type == "window_move":
                from .input_handlers.input import WindowMoveInput

                log.debug("使用基于窗口移动的后台点击模块")
                self.input_handler = WindowMoveInput()
        if self.input_handler is None:
            from .input_handlers.input import BackgroundInput

            self.input_handler = BackgroundInput()
        assert isinstance(
            self.input_handler, AbstractInput
        ), "输入处理器必须是AbstractInput的实例"
        self.mouse_click = self.input_handler.mouse_click
        self.mouse_click_blank = self.input_handler.mouse_click_blank
        self.mouse_drag = self.input_handler.mouse_drag
        self.mouse_drag_down = self.input_handler.mouse_drag_down
        self.mouse_scroll = self.input_handler.mouse_scroll
        self.set_pause = self.input_handler.set_pause
        self.wait_pause = self.input_handler.wait_pause
        self.mouse_to_blank = self.input_handler.mouse_to_blank
        self.mouse_drag_link = self.input_handler.mouse_drag_link
        self.key_press = self.input_handler.key_press
        self.input_text = self.input_handler.input_text
        self.memory_protection = cfg.memory_protection

    def check_pause(self) -> bool:
        """
        检查是否处于暂停状态

        Returns:
            bool: 是否处于暂停状态
        """
        return self.input_handler.is_pause

    def get_restore_time(self) -> float:
        """
        获取上一次结束暂停的时间
        Returns:
            float: 上一次结束暂停的时间
        """
        return self.input_handler.restore_time if self.input_handler.restore_time else 0

    def click_element(
        self,
        target,
        find_type="image",
        threshold=0.8,
        max_retries=1,
        take_screenshot=False,
        offset=True,
        action="click",
        times=1,
        dx=0,
        dy=0,
        model=None,
        my_crop=None,
        click=True,
        drag_time=None,
        interval=0.5,
    ):
        """查找并点击屏幕上的元素"""
        if model is None:
            model = self.model
        coordinates = self.find_element(
            target,
            find_type,
            threshold,
            max_retries,
            take_screenshot,
            model=model,
            my_crop=my_crop,
            additional_stack=1,
        )
        if coordinates:
            if click:
                return self.mouse_action_with_pos(
                    coordinates,
                    offset,
                    action,
                    times,
                    drag_time,
                    dx,
                    dy,
                    find_type,
                    interval,
                )
            return coordinates
        return False

    def calculate_click_position(self, coordinates, offset=True):
        """
        根据给定的坐标计算点击位置。
        参数:
        coordinates (tuple): 一个包含(x, y)坐标的元组，表示点击的位置。
        返回:
        tuple: 经过计算后的点击位置坐标。
        """
        # TODO:后续适配无需窗口设置模式
        x, y = coordinates
        screenshot = np.array(self.screenshot)
        if offset:
            # 使用正态分布生成点击偏移，使其更聚集在中心区域，符合人类点击习惯
            offset_x = int(np.clip(np.random.normal(0, 4), -10, 10))
            offset_y = int(np.clip(np.random.normal(0, 4), -10, 10))
            x = max(0, min(screenshot.shape[1], x + offset_x))
            y = max(0, min(screenshot.shape[0], y + offset_y))
        return x, y

    def mouse_action_with_pos(
        self,
        coordinates,
        offset=True,
        action="click",
        times=1,
        drag_time=None,
        dx=0,
        dy=0,
        find_type=None,
        interval=0.5,
    ) -> bool:
        """
        在指定坐标上执行点击操作
        Args:
            coordinates: 坐标位置，用于计算点击位置
            offset: 是否使用偏移量计算点击位置，默认为True
            action: 鼠标操作类型，默认为"click"
            move_back: 是否在操作后将鼠标移动回原位置，默认为False
        Returns:
           bool (True) : 总是返回True表示操作执行完毕
        """
        if find_type == "image_with_multiple_targets" and len(coordinates) > 0:
            for c in coordinates:
                self.mouse_action_with_pos(
                    c,
                    offset=offset,
                    action=action,
                    times=times,
                    drag_time=drag_time,
                    dx=dx,
                    dy=dy,
                    find_type="image",
                    interval=1,
                )
            return True

        if cfg.mouse_action_interval and interval == 0.5:
            interval = cfg.mouse_action_interval
        # Ensure we don't arbitrarily wait too long for consecutive fast clicks unless specified
        interval = min(interval, 0.25)

        # 增加随机浮动，规避匀速点击检测
        actual_interval = max(0.05, np.random.normal(interval, interval * 0.2))

        if self.last_click_time == 0:
            self.last_click_time = time.time()
        if time.time() - self.last_click_time < actual_interval:
            time.sleep(actual_interval)
            self.last_click_time = time.time()

        # 计算传入的位置
        x, y = self.calculate_click_position(coordinates, offset)

        # 定义鼠标操作映射
        action_map = {
            "click": self.mouse_click,
            "drag": self.mouse_drag,
            "drag_down": self.mouse_drag_down,
            "scroll": self.mouse_scroll,
        }
        # 根据操作类型执行相应的鼠标操作
        if action in action_map:
            if action == "click":
                self.mouse_click(x, y, times=times)
            elif action == "drag":
                self.mouse_drag(x, y, drag_time=drag_time, dx=dx, dy=dy)
            elif action == "drag_down":
                self.mouse_drag_down(x, y)
            elif action == "scroll":
                self.mouse_scroll()
            self.last_click_time = time.time()
        else:
            # 如果操作类型未知，抛出异常
            raise ValueError(f"未知的操作类型{action}")

        return True

    def take_screenshot(self, gray: bool = True) -> Image | None:
        """
        截取当前屏幕并返回图像对象。
        Args:
            gray (bool): 是否将图像转换为灰度图，默认为True。
        Returns:
            Image: 截取当前屏幕的图像对象
        """
        start_time = time.time()
        screenshot_interval_time = (
            cfg.screenshot_interval if cfg.screenshot_interval else 0.85
        )
        is_game_die = False
        while True:
            try:
                if time.time() - self.last_screenshot_time < screenshot_interval_time:
                    wait_time = max(
                        screenshot_interval_time
                        - (time.time() - self.last_screenshot_time),
                        0,
                    )
                    time.sleep(wait_time)

                result = ScreenShot.take_screenshot(gray)
                if result:
                    self.screenshot = result
                    self.last_screenshot_time = time.time()
                    return result
                else:
                    return None
            except withOutGameWinError as e:
                log.error(f"截图失败: {e}")
                is_game_die = True
            except Exception as e:
                log.error(f"截图失败:{e}")
            time.sleep(1)
            if time.time() - start_time > 60 or is_game_die:
                log.error("截图超时，尝试重启游戏")
                import os

                import win32process

                from module.game_and_screen import screen

                try:
                    _, pid = win32process.GetWindowThreadProcessId(screen.handle.hwnd)
                    os.system(f"taskkill /F /PID {pid}")
                except:
                    pass
                from tasks.base.script_task_scheme import init_game

                init_game()
                is_game_die = False
                start_time = time.time()

    def get_default_roi(self, target: Any) -> list[int] | None:
        """
        Define and return default Region of Interest (ROI) scan boundaries for specific elements to avoid full-screen scans.
        """
        if not isinstance(target, str):
            return None

        h = cfg.set_win_size
        w = int(h * 16 / 9)
        target_str = target.lower()

        # Shop grids/commodities
        if "mirror/shop/" in target_str or "shop_" in target_str or "purchase" in target_str:
            return [int(w * 0.10), int(h * 0.15), int(w * 0.95), int(h * 0.85)]

        # Road nodes/bus
        if "road_in_mir/" in target_str or "mybus" in target_str:
            return [0, int(h * 0.10), w, int(h * 0.90)]

        return None

    def _find_element_by_type(
        self, target, find_type, threshold, model, crop_area, min_dist, additional_stack
    ):
        if find_type == "image":
            return self.find_image_element(
                target,
                threshold,
                model=model,
                my_crop=crop_area,
                additional_stack=additional_stack + 1,
            )
        elif find_type == "text":
            return self.find_text_element(
                target, crop_area, additional_stack=additional_stack + 1
            )
        elif find_type == "feature":
            return self.find_feature_element(
                target, crop_area, additional_stack=additional_stack + 1
            )
        elif find_type == "image_with_multiple_targets":
            return self.find_image_with_multiple_targets(
                target,
                threshold,
                my_crop=crop_area,
                min_dist=min_dist,
                additional_stack=additional_stack + 1,
            )
        else:
            raise ValueError(f"错误的类型: {find_type}")

    def find_element(
        self,
        target,
        find_type="image",
        threshold=0.8,
        max_retries=1,
        take_screenshot=False,
        model=None,
        my_crop=None,
        min_dist=10,
        additional_stack=0,
        roi=None,
    ):
        """
        查找元素，并根据指定的查找类型执行不同的查找策略。
        """
        if model is None:
            model = self.model

        effective_crop = my_crop if my_crop is not None else roi

        # Enforce Region of Interest (ROI) boundaries for specific elements if no custom crop is specified
        if effective_crop is None:
            effective_crop = self.get_default_roi(target)

        if not hasattr(self, "location_cache"):
            self.location_cache = {}

        max_retries = 1 if not take_screenshot else max_retries
        for i in range(max_retries):
            if take_screenshot:
                while self.take_screenshot() is None:
                    continue

            # Check location matching cache for hashable single-target types
            is_cacheable = (
                find_type in ["image", "text"]
                and isinstance(target, (str, int, float))
                and not (isinstance(target, str) and target.endswith("assets.png"))
            )

            if is_cacheable and target in self.location_cache:
                cached_pos = self.location_cache[target]
                h = cfg.set_win_size
                w = int(h * 16 / 9)
                x, y = cached_pos
                
                # Dynamically set padding to prevent template mismatch size errors
                padding = 100
                if find_type == "image":
                    existing_paths = ImageUtils.existing_image_paths(target)
                    if existing_paths:
                        cache_key = (target, existing_paths[0])
                        if cache_key in self.img_cache:
                            template = self.img_cache[cache_key]["template"]
                            if template is not None:
                                padding = max(template.shape[1] // 2 + 30, template.shape[0] // 2 + 30, 50)
                
                x1 = max(0, int(x - padding))
                y1 = max(0, int(y - padding))
                x2 = min(w, int(x + padding))
                y2 = min(h, int(y + padding))
                micro_roi = (x1, y1, x2, y2)

                center = self._find_element_by_type(
                    target, find_type, threshold, model, micro_roi, min_dist, additional_stack
                )
                if center:
                    self.location_cache[target] = center
                    return center

            # Fall back to standard/enforced ROI search
            center = self._find_element_by_type(
                target, find_type, threshold, model, effective_crop, min_dist, additional_stack
            )

            if center:
                if is_cacheable:
                    self.location_cache[target] = center
                return center
            else:
                if is_cacheable:
                    self.location_cache.pop(target, None)

            if i < max_retries - 1:
                time.sleep(1)
        return None

    def find_image_with_multiple_targets(
        self, target: str, threshold, my_crop=None, min_dist=10, additional_stack=0
    ) -> List:
        """
        在当前截图中查找多个目标图像的位置
        """
        try:
            template = ImageUtils.load_image(target)
            if target.endswith("assets.png"):
                bbox = ImageUtils.get_bbox(template)
                template = ImageUtils.crop(template, bbox)
            if template is None:
                raise ValueError("读取图片失败")
            screenshot = np.array(self.screenshot)
            crop_offset = (0, 0)
            if my_crop:
                crop_offset = (int(round(my_crop[0])), int(round(my_crop[1])))
                screenshot = ImageUtils.crop(screenshot, my_crop)
            if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
                return []
            matches = ImageUtils.match_template_with_multiple_targets(
                screenshot, template, threshold, min_dist=min_dist
            )
            if crop_offset != (0, 0):
                matches = [(x + crop_offset[0], y + crop_offset[1]) for x, y in matches]
            if len(matches) == 0:
                log.debug(
                    f"未找到任何目标图像{target}", stacklevel=additional_stack + 3
                )
                return []
            else:
                log.debug(
                    f"找到{len(matches)}个目标：{matches}",
                    stacklevel=additional_stack + 3,
                )
                return matches
        except Exception as e:
            log.error(f"寻找图片出错:{e}")
            return []

    def find_str_in_text(self, target, ocr_dict):
        """
        返回目标文本的坐标
        """
        for text in ocr_dict.keys():
            if target.lower() in text.lower():
                log.debug(f"识别到目标：{text},坐标为：{ocr_dict[text]}")
                return ocr_dict[text]
            # 去除空格后再匹配，解决OCR识别结果带空格的问题（如 "HongLu" vs "Hong Lu"）
            if target.replace(" ", "").lower() in text.replace(" ", "").lower():
                log.debug(f"识别到目标（去空格匹配）：{text},坐标为：{ocr_dict[text]}")
                return ocr_dict[text]
        return False

    def _run_ocr_for_text(self, my_crop=None, only_text=False, additional_stack=0):
        crop_offset = (0, 0)
        if my_crop is not None:
            crop_offset = (int(round(my_crop[0])), int(round(my_crop[1])))
            cropped_image = self.screenshot.crop(my_crop)
            ocr_result = ocr.run(cropped_image)
        else:
            ocr_result = ocr.run(self.screenshot)

        if not ocr_result.txts:
            return False if only_text else {}

        ocr_text_list = [ocr_result.txts[i] for i in range(len(ocr_result.txts))]
        if only_text:
            return ocr_text_list

        ocr_position_list = []
        for box in ocr_result.boxes:
            x = (box[0][0] + box[2][0]) / 2 + crop_offset[0]
            y = (box[0][1] + box[2][1]) / 2 + crop_offset[1]
            ocr_position_list.append([x, y])

        ocr_dict = {
            text: position for text, position in zip(ocr_text_list, ocr_position_list)
        }
        log.debug(f"识别到文本及其坐标：{ocr_dict}", stacklevel=additional_stack + 3)
        return ocr_dict

    def _find_target_in_ocr_dict(self, target, ocr_dict, all_text=False):
        if ocr_dict == {}:
            return False
        if isinstance(target, str):
            return self.find_str_in_text(target, ocr_dict)
        elif isinstance(target, list):
            if all_text:
                for key in target:
                    if self.find_str_in_text(str(key), ocr_dict) is False:
                        return False
                return True
            for key in target:
                if result := self.find_str_in_text(str(key), ocr_dict):
                    return result
            return False
        elif isinstance(target, dict):
            for key, value in target.items():
                if position := self.find_str_in_text(str(key), ocr_dict):
                    return TextMatchResult(
                        value=value, text=str(key), position=position
                    )
            return None
        return False

    def find_language_text(
        self,
        zh_text,
        en_text,
        my_crop=None,
        all_text=False,
        additional_stack=0,
    ):
        """
        按当前语言状态查找中英文文本，并在语言未知时用命中结果同步语言。

        该方法只执行一次 OCR，然后在同一份 OCR 结果中匹配文本：
        - 当前语言为 zh_cn 时，只匹配 zh_text。
        - 当前语言为 en 时，只匹配 en_text。
        - 当前语言未知时，先匹配 zh_text；中文命中则同步语言为 zh_cn。
        - 中文未命中时再匹配 en_text；英文命中则同步语言为 en，并移除 zh_cn 图片路径。

        Args:
            zh_text: 中文目标文本，支持 str、list、dict，规则同 find_text_element。
            en_text: 英文目标文本，支持 str、list、dict，规则同 find_text_element。
            my_crop: OCR 裁剪区域，格式为 (x1, y1, x2, y2)；为 None 时识别整张截图。
            all_text: 当目标文本为 list 时，是否要求列表内所有关键词全部命中。
            additional_stack: 日志 stacklevel 补偿，用于让日志定位到业务调用处。

        Returns:
            文本命中结果，返回格式同 find_text_element；未命中返回 False。
        """
        ocr_dict = self._run_ocr_for_text(
            my_crop=my_crop, additional_stack=additional_stack
        )
        if ocr_dict == {}:
            return False

        if path_manager.current_language == "zh_cn":
            return self._find_target_in_ocr_dict(zh_text, ocr_dict, all_text=all_text)
        if path_manager.current_language == "en":
            return self._find_target_in_ocr_dict(en_text, ocr_dict, all_text=all_text)

        zh_result = self._find_target_in_ocr_dict(zh_text, ocr_dict, all_text=all_text)
        if zh_result is not False and zh_result is not None:
            path_manager.set_language("zh_cn", log_stacklevel=additional_stack + 4)
            return zh_result

        en_result = self._find_target_in_ocr_dict(en_text, ocr_dict, all_text=all_text)
        if en_result is not False and en_result is not None:
            path_manager.set_language("en", log_stacklevel=additional_stack + 4)
            if path_manager.eliminate_zh_cn_paths():
                self.clear_img_cache()
            return en_result

        return False

    def find_text_element(
        self, target, my_crop=None, all_text=False, only_text=False, additional_stack=0
    ):
        """
        寻找文本元素所在的坐标位置。

        str/list 目标返回坐标；dict 目标返回 TextMatchResult。
        """
        ocr_result = self._run_ocr_for_text(
            my_crop=my_crop, only_text=only_text, additional_stack=additional_stack
        )
        if only_text:
            return ocr_result
        return self._find_target_in_ocr_dict(target, ocr_result, all_text=all_text)

    def get_text_from_screenshot(self, my_crop=None):
        """
        从屏幕截图中提取文字
        """
        if my_crop is not None:
            # 根据my_crop（为左上与右下四个坐标），截取self.screenshot的部分区域进行ocr
            cropped_image = self.screenshot.crop(my_crop)
            ocr_result = ocr.run(cropped_image)
        else:
            ocr_result = ocr.run(self.screenshot)
        if ocr_result.txts:
            ocr_text_list = [ocr_result.txts[i] for i in range(len(ocr_result.txts))]
        else:
            ocr_text_list = []

        return ocr_text_list

    def find_feature_element(
        self, target, pic_crop=None, min_matches=8, additional_stack=0
    ):
        """
        寻找特征元素所在的坐标位置（优化为使用多尺度模板匹配）
        """
        try:
            template = ImageUtils.load_image(target, resize=False)
            if template is None:
                return None
            screenshot = np.array(self.screenshot)
            crop_offset = (0, 0)
            if pic_crop:
                scaled_crop = list(pic_crop)
                if cfg.set_win_size < 1440:
                    scaled_crop = [int(i * 1440 / cfg.set_win_size) for i in scaled_crop]
                elif cfg.set_win_size > 1440:
                    scaled_crop = [int(i * cfg.set_win_size / 1440) for i in scaled_crop]
                crop_offset = (scaled_crop[0], scaled_crop[1])
                screenshot = ImageUtils.crop(screenshot, scaled_crop)
            
            if len(screenshot.shape) == 3:
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
            else:
                screenshot_gray = screenshot

            scales = [0.85, 1.0, 1.15]
            best_match_val = -1
            best_center = None

            for scale in scales:
                if scale == 1.0:
                    scaled_template = template
                else:
                    h_t, w_t = template.shape[:2]
                    new_h, new_w = int(h_t * scale), int(w_t * scale)
                    if new_h <= 0 or new_w <= 0 or new_h > screenshot_gray.shape[0] or new_w > screenshot_gray.shape[1]:
                        continue
                    scaled_template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)

                if scaled_template.shape[0] > screenshot_gray.shape[0] or scaled_template.shape[1] > screenshot_gray.shape[1]:
                    continue

                res = cv2.matchTemplate(screenshot_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > best_match_val:
                    best_match_val = max_val
                    h_st, w_st = scaled_template.shape[:2]
                    best_center = (
                        int(max_loc[0]) + w_st // 2 + crop_offset[0],
                        int(max_loc[1]) + h_st // 2 + crop_offset[1]
                    )

            threshold = 0.70
            matched = best_match_val >= threshold
            log.debug(
                f"优化特征匹配：{target.replace('./assets/images/', '')}，最佳相似度：{best_match_val:.3f}，结果：{matched}",
                stacklevel=additional_stack + 3,
            )
            if matched:
                return best_center
            return None
        except Exception as e:
            log.error(f"匹配图片特征失败:{e}")
            return None

    def clear_img_cache(self) -> None:
        """清除图片缓存"""
        if not self.img_cache and not getattr(self, "location_cache", None):
            return
        self.img_cache.clear()
        if hasattr(self, "location_cache"):
            self.location_cache.clear()
        gc.collect()  # 强制垃圾回收，清理内存
        log.debug("图片缓存已清除", stacklevel=2)

    def _load_template_for_path(self, target: str, target_path: str, cacheable: bool):
        cache_key = (target, target_path)
        if cacheable and cache_key in self.img_cache:
            cached = self.img_cache[cache_key]
            return cached["template"], cached["bbox"]

        template = ImageUtils.load_from_specific_path(target, target_path)
        if template is None:
            return None, None
        if target.endswith("assets.png"):
            bbox = ImageUtils.get_bbox(template)
            template = ImageUtils.crop(template, bbox)
        else:
            bbox = None
        if cacheable:
            self.img_cache[cache_key] = {"template": template, "bbox": bbox}
        return template, bbox

    @staticmethod
    def _is_valid_match(match_val, threshold) -> bool:
        return (
            isinstance(match_val, (int, float, np.integer, np.floating))
            and not math.isinf(match_val)
            and match_val >= threshold
        )

    MATCH_GAP = 0.15

    def _update_path_state_from_match_results(
        self, results, additional_stack: int = 0
    ) -> None:
        dark_results = [
            result for result in results if path_manager.is_path_dark(result["path"])
        ]
        default_results = [
            result for result in results if path_manager.is_path_default(result["path"])
        ]
        zh_cn_results = [
            result for result in results if path_manager.is_path_zh_cn(result["path"])
        ]
        en_results = [result for result in results if result["path"].endswith("/en")]
        share_results = [
            result for result in results if result["path"].endswith("/share")
        ]

        dark_matched = any(result["matched"] for result in dark_results)
        default_matched = any(result["matched"] for result in default_results)

        path_changed = False
        if dark_matched and not default_matched:
            path_manager.set_theme("dark", log_stacklevel=additional_stack + 4)
        elif default_matched and dark_results and not dark_matched:
            path_manager.set_theme("default", log_stacklevel=additional_stack + 4)
        elif dark_matched and default_matched:
            best_dark = max(r["matchVal"] for r in dark_results if r["matched"])
            best_default = max(r["matchVal"] for r in default_results if r["matched"])
            if best_default - best_dark > self.MATCH_GAP:
                path_manager.set_theme("default", log_stacklevel=additional_stack + 4)
            elif best_dark - best_default > self.MATCH_GAP:
                path_manager.set_theme("dark", log_stacklevel=additional_stack + 4)

        zh_cn_matched = any(result["matched"] for result in zh_cn_results)
        en_matched = any(result["matched"] for result in en_results)
        share_matched = any(result["matched"] for result in share_results)

        # share 路径是语言无关资源，不能单独决定语言为英文
        if zh_cn_matched and not en_matched:
            path_manager.set_language("zh_cn", log_stacklevel=additional_stack + 4)
        elif en_matched and not zh_cn_matched:
            path_manager.set_language("en", log_stacklevel=additional_stack + 4)
            path_changed = path_manager.eliminate_zh_cn_paths() or path_changed
        elif zh_cn_matched and en_matched:
            best_zh = max(r["matchVal"] for r in zh_cn_results if r["matched"])
            best_en = max(r["matchVal"] for r in en_results if r["matched"])
            if best_en - best_zh > self.MATCH_GAP:
                path_manager.set_language("en", log_stacklevel=additional_stack + 4)
                path_changed = path_manager.eliminate_zh_cn_paths() or path_changed
            elif best_zh - best_en > self.MATCH_GAP:
                path_manager.set_language("zh_cn", log_stacklevel=additional_stack + 4)
        elif share_matched:
            # 仅命中 share 时保持当前语言未知/不变，等待后续专属语言资源判定
            pass

        if path_changed:
            self.clear_img_cache()

    @staticmethod
    def _path_state_is_known() -> bool:
        return (
            path_manager.current_theme is not None
            and path_manager.current_language is not None
        )

    def find_image_element(
        self,
        target: str,
        threshold,
        cacheable=True,
        model="clam",
        my_crop=None,
        additional_stack=0,
    ):
        """
        在当前截图中查找目标图像的位置
        """
        try:
            if self.memory_protection:
                now = time.time()
                if now - self.last_memory_check_time > 10:
                    self.last_memory_check_time = now
                    memory = psutil.virtual_memory()
                    current_percent = memory.percent
                    if current_percent > 90:
                        has_cache = bool(self.img_cache) or bool(getattr(self, "location_cache", None))
                        if has_cache:
                            log.debug(f"当前系统内存总占用率: {current_percent}%，释放图片缓存")
                            self.clear_img_cache()

            existing_paths = ImageUtils.existing_image_paths(target)
            if not existing_paths:
                log.error(f"未找到图片： {target} ")
                log.debug(f"无法加载图片: {target}", stacklevel=additional_stack + 3)
                return None

            screenshot = np.array(self.screenshot)
            crop_offset = (0, 0)
            if my_crop:
                crop_offset = (int(round(my_crop[0])), int(round(my_crop[1])))
                screenshot = ImageUtils.crop(screenshot, my_crop)

            results = []
            for loaded_path in existing_paths:
                template, bbox = self._load_template_for_path(
                    target, loaded_path, cacheable
                )
                if template is None:
                    continue
                center, matchVal = ImageUtils.match_template(
                    screenshot, template, bbox, model
                )
                matched = self._is_valid_match(matchVal, threshold)
                if 0.70 < matchVal < 0.90 and int(matchVal * 1000 + 1e-9) % 10 >= 5:
                    match_fmt = ".3f"
                else:
                    match_fmt = ".2f"
                log.debug(
                    f"目标图片：{target.replace('./assets/images/', '')}, 路径: {loaded_path}, 相似度：{matchVal:{match_fmt}}, 目标位置：{center}",
                    stacklevel=additional_stack + 3,
                )
                results.append(
                    {
                        "path": loaded_path,
                        "center": (center[0] + crop_offset[0], center[1] + crop_offset[1]) if center else None,
                        "matched": matched,
                        "matchVal": matchVal,
                    }
                )
                if matched and self._path_state_is_known():
                    return results[-1]["center"]

            if not results:
                log.debug(f"无法加载图片: {target}", stacklevel=additional_stack + 3)
                return None

            self._update_path_state_from_match_results(
                results, additional_stack=additional_stack
            )
            for result in results:
                if result["matched"]:
                    return result["center"]
        except Exception as e:
            log.error(f"寻找图片失败:{e}")
        return None

    def get_screenshot_crop(self, crop):
        """
        获取指定区域的彩色截图
        """
        self.take_screenshot(False)
        screenshot = np.array(self.screenshot)
        screenshot = screenshot[:, :, ::-1]
        screenshot = ImageUtils.crop(screenshot, crop)
        return screenshot

    def wait_until_appear(
        self,
        target,
        timeout=10,
        poll_interval=0.5,
        find_type="image",
        threshold=0.8,
        my_crop=None,
        roi=None,
    ):
        """
        Wait until target element appears on the screen.
        Uses active dynamic polling instead of rigid sleep delays.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.take_screenshot() is None:
                time.sleep(poll_interval)
                continue
            pos = self.find_element(
                target=target,
                find_type=find_type,
                threshold=threshold,
                take_screenshot=False,
                my_crop=my_crop,
                roi=roi,
            )
            if pos:
                return pos
            time.sleep(poll_interval)
        return None


class GameState:
    MAIN_MENU = "MAIN_MENU"
    MIRROR_ENTRANCE = "MIRROR_ENTRANCE"
    ROAD_MAP = "ROAD_MAP"
    SHOP = "SHOP"
    EVENT = "EVENT"
    BATTLE_FORMATION = "BATTLE_FORMATION"
    BATTLE = "BATTLE"
    THEME_PACK = "THEME_PACK"
    EGO_GIFT_SELECT = "EGO_GIFT_SELECT"
    CLAIM_REWARD = "CLAIM_REWARD"
    UNKNOWN = "UNKNOWN"


class PageStateDispatcher:
    """Page-Based State Dispatcher with unique pixel/image anchors for game states."""

    def __init__(self, automation_instance=None):
        from module.automation.automation import Automation
        self.auto = automation_instance if automation_instance else Automation("AhabAssistant")

    def detect_state(self) -> str:
        """
        Detects the current game state / page based on screen content.
        Uses cached templates/anchors for quick page recognition.
        """
        if self.auto.screenshot is None:
            self.auto.take_screenshot()

        # Priority order checks
        if (self.auto.find_element("battle/more_information_assets.png") or
            self.auto.find_element("battle/in_mirror_assets.png") or
            self.auto.find_element("battle/win_rate_card.png") or
            self.auto.find_element("battle/turn_assets.png")):
            return GameState.BATTLE

        if self.auto.find_element("teams/identify_assets.png"):
            return GameState.BATTLE_FORMATION

        if self.auto.find_element("mirror/shop/shop_coins_assets.png"):
            return GameState.SHOP

        if self.auto.find_element("mirror/road_in_mir/legend_assets.png"):
            return GameState.ROAD_MAP

        if self.auto.find_element("mirror/theme_pack/feature_theme_pack_assets.png"):
            return GameState.THEME_PACK

        if (self.auto.find_element("mirror/road_in_mir/acquire_ego_gift_card.png") or
            self.auto.find_element("mirror/road_in_mir/acquire_ego_gift_box_assets.png") or
            self.auto.find_element("mirror/road_in_mir/acquire_ego_gift_refuse_assets.png")):
            return GameState.EGO_GIFT_SELECT

        if (self.auto.find_element("mirror/claim_reward/battle_statistics_assets.png") or
            self.auto.find_element("mirror/claim_reward/claim_rewards_assets.png") or
            self.auto.find_element("mirror/claim_reward/complete_mirror_100%_assets.png") or
            self.auto.find_element("mirror/claim_reward/use_enkephalin_assets.png")):
            return GameState.CLAIM_REWARD

        if self.auto.find_element("event/skip_assets.png"):
            return GameState.EVENT

        if (self.auto.find_element("mirror/road_to_mir/enter_assets.png") or
            self.auto.find_element("mirror/road_to_mir/resume_assets.png") or
            self.auto.find_element("mirror/road_to_mir/enter_mirror_assets.png")):
            return GameState.MIRROR_ENTRANCE

        if (self.auto.find_element("home/drive_assets.png") or
            self.auto.find_element("home/window_assets.png")):
            return GameState.MAIN_MENU

        return GameState.UNKNOWN

