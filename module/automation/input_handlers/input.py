import random
import numpy as np
from time import sleep, time
from typing import overload

import pyautogui
import pyperclip
import win32api
import win32con
import win32gui
from pywintypes import error as PyWinTypesError

from module.config import cfg
from utils.singletonmeta import SingletonMeta

from ...game_and_screen import screen
from ...logger import log
from . import AbstractInput
from .bezier import generate_bezier_path
from .delay import humanised_delay
from .driver_interface import InputDriver

key_list = {
    "a": 0x41,
    "b": 0x42,
    "c": 0x43,
    "d": 0x44,
    "e": 0x45,
    "f": 0x46,
    "g": 0x47,
    "h": 0x48,
    "i": 0x49,
    "j": 0x4A,
    "k": 0x4B,
    "l": 0x4C,
    "m": 0x4D,
    "n": 0x4E,
    "o": 0x4F,
    "p": 0x50,
    "q": 0x51,
    "r": 0x52,
    "s": 0x53,
    "t": 0x54,
    "u": 0x55,
    "v": 0x56,
    "w": 0x57,
    "x": 0x58,
    "y": 0x59,
    "z": 0x5A,
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "enter": win32con.VK_RETURN,
    "esc": win32con.VK_ESCAPE,
    "space": win32con.VK_SPACE,
    "tab": win32con.VK_TAB,
    "shift": win32con.VK_SHIFT,
    "ctrl": win32con.VK_CONTROL,
    "alt": win32con.VK_MENU,
    "up": win32con.VK_UP,
    "down": win32con.VK_DOWN,
    "left": win32con.VK_LEFT,
    "right": win32con.VK_RIGHT,
}

EXTENDED_KEY_VKS = frozenset(
    {
        win32con.VK_UP,
        win32con.VK_DOWN,
        win32con.VK_LEFT,
        win32con.VK_RIGHT,
        win32con.VK_HOME,
        win32con.VK_END,
        win32con.VK_PRIOR,
        win32con.VK_NEXT,
        win32con.VK_INSERT,
        win32con.VK_DELETE,
        win32con.VK_RCONTROL,
        win32con.VK_RMENU,
        win32con.VK_LWIN,
        win32con.VK_RWIN,
    }
)

MESSAGE_KEY_WPARAMS = {
    win32con.VK_LCONTROL: win32con.VK_CONTROL,
    win32con.VK_RCONTROL: win32con.VK_CONTROL,
    win32con.VK_LMENU: win32con.VK_MENU,
    win32con.VK_RMENU: win32con.VK_MENU,
}


class WinAbstractInput(AbstractInput):
    """输入接口类，定义输入方法的抽象接口
    专用于 Windows 系统, 提供了一些额外的通用方法

    Tips: 有特殊需求写在对应方法描述中
    """

    def __init__(self, driver: InputDriver | None = None) -> None:
        super().__init__()
        self.use_post_message = cfg.config.use_post_message
        self.driver = driver

    def set_driver(self, driver: InputDriver | None) -> None:
        self.driver = driver

    def get_driver(self) -> InputDriver | None:
        return self.driver

    def get_mouse_position(self) -> tuple[int, int]:
        """获取鼠标当前位置

        Returns:
            tuple: 当前鼠标位置的元组 (x, y)，锁屏时返回 (0, 0)
        """
        try:
            return win32api.GetCursorPos()
        except PyWinTypesError:
            log.debug("获取鼠标位置失败（可能锁屏），返回 (0, 0)")
            return (0, 0)

    @staticmethod
    def _make_key_lparam(vk: int, key_up: bool = False) -> int:
        """构造 WM_KEYDOWN/UP 的正确 lParam。

        Unity 6+ 会校验 scan code 和 extended flag，
        固定 0x00000001 / 0xC0000001 的消息会被忽略。
        """
        scan = win32api.MapVirtualKey(vk, 0) & 0xFF
        extended = vk in EXTENDED_KEY_VKS
        lparam = 1 | (scan << 16)
        if extended:
            lparam |= 1 << 24
        if key_up:
            lparam |= (1 << 30) | (1 << 31)
        return lparam

    @staticmethod
    def _make_key_wparam(vk: int) -> int:
        return MESSAGE_KEY_WPARAMS.get(vk, vk)


def human_delay(base_time=0.1, std_dev=0.03):
    """生成正态分布的随机延迟，更符合人类操作习惯，下限保护为0.01"""
    delay = np.random.normal(base_time, std_dev)
    return max(0.01, delay)


class Input(WinAbstractInput, metaclass=SingletonMeta):
    """基于 `pyautogui` 的输入类, 仅支持前台操作"""

    # 禁用pyautogui的失败安全特性，防止意外中断
    pyautogui.FAILSAFE = False

    @overload
    def pos_offset(self, x: int, y: int) -> tuple[int, int]: ...
    @overload
    def pos_offset(self, pos: tuple[int, int]) -> tuple[int, int]: ...

    def pos_offset(self, *args) -> tuple[int, int]:  # type: ignore
        """根据当前窗口位置偏移点击位置"""
        if len(args) == 2:
            x, y = args
        elif isinstance(args[0], tuple):
            x, y = args[0]
        else:
            raise ValueError("pos_offset 接受两个整数参数或一个包含两个整数的元组")
        real_x, real_y, _, _ = screen.handle.rect(True)
        return x + real_x, y + real_y

    def mouse_click(self, x, y, times=1, move_back=False) -> bool:
        if move_back:
            current_mouse_position = self.get_mouse_position()

        msg = f"点击位置:({x},{y})"
        log.debug(msg, stacklevel=2)
        x, y = self.pos_offset(x, y)
        self.mouse_move((x, y))
        for i in range(times):
            if self.driver:
                self.driver.mouse_down(x, y)
                sleep(humanised_delay(0.05, "gaussian"))
                self.driver.mouse_up(x, y)
            else:
                pyautogui.mouseDown(x, y)
                sleep(humanised_delay(0.05, "gaussian"))
                pyautogui.mouseUp(x, y)
            if times > 1 and i < times - 1:
                sleep(humanised_delay(0.1, "gaussian"))

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

        self.wait_pause()

        return True

    def mouse_drag_down(self, x, y, reverse=1, move_back=True) -> None:
        if move_back:
            current_mouse_position = self.get_mouse_position()

        scale = cfg.set_win_size / 1080
        x, y = self.pos_offset(x, y)
        self.mouse_move((x, y))
        if self.driver:
            self.driver.mouse_down(x, y)
        else:
            pyautogui.mouseDown()
        
        end_y = y + int(300 * scale * reverse)
        path = generate_bezier_path((x, y), (x, end_y))
        step_time = 0.4 / max(1, len(path))
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                pyautogui.moveTo(px, py)
            sleep(humanised_delay(step_time, "gaussian"))
            
        if self.driver:
            self.driver.mouse_up(x, end_y)
        else:
            pyautogui.mouseUp()

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def mouse_drag(self, x, y, drag_time=0.1, dx=0, dy=0, move_back=True) -> None:
        if move_back:
            current_mouse_position = self.get_mouse_position()
        x, y = self.pos_offset(x, y)
        self.mouse_move((x, y))
        if self.driver:
            self.driver.mouse_down(x, y)
        else:
            pyautogui.mouseDown()
            
        path = generate_bezier_path((x, y), (x + dx, y + dy))
        step_time = drag_time / max(1, len(path))
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                pyautogui.moveTo(px, py)
            sleep(humanised_delay(step_time, "gaussian"))
            
        # 注入随机拖拽延迟
        sleep(humanised_delay(drag_time * 0.3 if drag_time * 0.3 > 0.2 else 0.2, "gaussian"))
        if self.driver:
            self.driver.mouse_up(x + dx, y + dy)
        else:
            pyautogui.mouseUp()

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def mouse_scroll(self, direction: int = -3) -> bool:
        if direction <= 0:
            msg = "鼠标滚动滚轮，远离界面"
        else:
            msg = "鼠标滚动滚轮，拉近界面"
        log.debug(msg, stacklevel=2)
        pyautogui.scroll(direction)
        return True

    def mouse_click_blank(self, coordinate=(1, 1), times=1, move_back=False) -> bool:
        if move_back:
            current_mouse_position = self.get_mouse_position()

        msg = "点击（1，1）空白位置"
        log.debug(msg, stacklevel=2)
        x = coordinate[0] + random.randint(0, 10)
        y = coordinate[1] + random.randint(0, 10)
        self.mouse_click(x, y, times=times, move_back=False)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

        self.wait_pause()
        return True

    def mouse_to_blank(self, coordinate=(1, 1), move_back=False) -> None:
        if move_back:
            current_mouse_position = self.get_mouse_position()

        msg = "鼠标移动到空白，避免遮挡"
        log.debug(msg, stacklevel=2)
        self.mouse_move(coordinate)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)
        self.wait_pause()

    def mouse_move(self, coordinate=(1, 1)) -> None:
        """鼠标移动到指定坐标

        Args:
            coordinate (tuple): 坐标元组 (x, y)
        """
        start_pos = self.get_mouse_position()
        target_pos = (coordinate[0], coordinate[1])
        path = generate_bezier_path(start_pos, target_pos)
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                pyautogui.moveTo(px, py)
            sleep(humanised_delay(0.005, "gaussian"))
        self.wait_pause()

    def mouse_drag_link(self, position: list, drag_time=0.1, move_back=False) -> None:
        if move_back:
            current_mouse_position = self.get_mouse_position()

        x, y = self.pos_offset(position[0][0], position[0][1])
        self.mouse_move((x, y))
        if self.driver:
            self.driver.mouse_down(x, y)
        else:
            pyautogui.mouseDown()
            
        curr_x, curr_y = x, y
        for pos in position:
            tx, ty = self.pos_offset(pos[0], pos[1])
            path = generate_bezier_path((curr_x, curr_y), (tx, ty))
            step_time = drag_time / max(1, len(path))
            for px, py in path:
                if self.driver:
                    self.driver.mouse_move(px, py)
                else:
                    pyautogui.moveTo(px, py)
                sleep(humanised_delay(step_time, "gaussian"))
            curr_x, curr_y = tx, ty
            
        if self.driver:
            self.driver.mouse_up(curr_x, curr_y)
        else:
            pyautogui.mouseUp()

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def key_press(self, key):
        if self.driver:
            self.driver.key_down(key)
            sleep(humanised_delay(0.05, "gaussian"))
            self.driver.key_up(key)
        else:
            return pyautogui.press(key)

class BackgroundInput(WinAbstractInput, metaclass=SingletonMeta):
    """基于 `pywin32` 的输入类, 支持后台操作
    \n 除了不支持滚轮事件, 其余同 `Input` 类
    """

    def __init__(self, driver: InputDriver | None = None) -> None:
        super().__init__(driver)
        self.last_x = 0
        self.last_y = 0

    def _post_bezier_move(self, target_x: int, target_y: int) -> None:
        start_pos = (self.last_x, self.last_y)
        target_pos = (target_x, target_y)
        path = generate_bezier_path(start_pos, target_pos)
        hwnd = screen.handle.hwnd
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                long_position = win32api.MAKELONG(px, py)
                if self.use_post_message:
                    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, long_position)
                else:
                    win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, long_position)
            sleep(humanised_delay(0.005, "gaussian"))
        self.last_x = target_x
        self.last_y = target_y

    def mouse_to_blank(self, coordinate=(1, 1), move_back=True) -> None:
        """鼠标移动到空白位置，避免遮挡"""
        # 后台模式下，只向窗口发送后台鼠标移动消息，不移动物理鼠标，避免干扰用户并导致Unity点击坐标漂移
        self._post_bezier_move(coordinate[0], coordinate[1])
        log.debug("鼠标移动到空白，避免遮挡", stacklevel=2)
        self.wait_pause()

    def mouse_click(self, x, y, times=1, move_back=True) -> bool:
        """在指定坐标上执行点击操作

        Args:
            x (int): x坐标
            y (int): y坐标
            times (int): 点击次数
            move_back (bool): 是否在点击后将鼠标移动回原位置
        Returns:
            bool (True) : 总是返回True表示操作执行完毕
        """
        if move_back:
            current_mouse_position = self.get_mouse_position()

        msg = f"点击位置:({x},{y})"
        log.debug(msg, stacklevel=2)
        for i in range(times):
            self.set_mouse_pos(x, y)
            self.set_active()
            self.mouse_down(x, y)
            sleep(humanised_delay(0.05, "gaussian"))  # 模拟人类按下和松开的时间间隔
            self.mouse_up(x, y)
            if times > 1 and i < times - 1:
                sleep(humanised_delay(0.1, "gaussian"))

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

        self.wait_pause()

        return True

    def mouse_drag_down(self, x, y, reverse=1, move_back=True) -> None:
        """鼠标从指定位置向下拖动

        Args:
            x (int): x坐标
            y (int): y坐标
            reverse (int): 拖动方向，1表示向下，-1表示向上
            move_back (bool): 是否在拖动后将鼠标移动回原位置
        """
        if move_back:
            current_mouse_position = self.get_mouse_position()

        scale = cfg.set_win_size / 1080
        self.set_active()
        self._post_bezier_move(x, y)
        self.mouse_down(x, y)
        end_y = y + int(300 * scale * reverse)
        
        path = generate_bezier_path((x, y), (x, end_y))
        hwnd = screen.handle.hwnd
        step_time = 0.4 / max(1, len(path))
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                long_position = win32api.MAKELONG(px, py)
                wparam = win32con.MK_LBUTTON
                if self.use_post_message:
                    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, long_position)
                else:
                    win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, long_position)
            sleep(humanised_delay(step_time, "gaussian"))
            
        self.last_x = x
        self.last_y = end_y
        self.mouse_up(x, end_y)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def mouse_drag(self, x, y, drag_time=0.1, dx=0, dy=0, move_back=True) -> None:
        """鼠标从指定位置拖动到另一个位置
        Args:
            x (int): 起始x坐标
            y (int): 起始y坐标
            drag_time (float): 拖动时间
            dx (int): x方向拖动距离
            dy (int): y方向拖动距离
            move_back (bool): 是否在拖动后将鼠标移动回原位置
        """
        if move_back:
            current_mouse_position = self.get_mouse_position()
        self.set_active()
        self._post_bezier_move(x, y)
        self.mouse_down(x, y)
        
        path = generate_bezier_path((x, y), (x + dx, y + dy))
        hwnd = screen.handle.hwnd
        step_time = drag_time / max(1, len(path))
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                long_position = win32api.MAKELONG(px, py)
                wparam = win32con.MK_LBUTTON
                if self.use_post_message:
                    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, long_position)
                else:
                    win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, long_position)
            sleep(humanised_delay(step_time, "gaussian"))
            
        self.last_x = x + dx
        self.last_y = y + dy
        # 注入随机拖拽延迟
        sleep(humanised_delay(drag_time * 0.3 if drag_time * 0.3 > 0.2 else 0.2, "gaussian"))
        self.mouse_up(x + dx, y + dy)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def mouse_scroll(self, direction: int = -3) -> bool:
        """
        不支持的方法\n
        进行鼠标滚动操作
        Args:
            direction (int): 滚动方向，正值表示拉近，负值表示缩小
        Returns:
            bool (False) : 表示是否支持该操作
        """
        # 不支持的方法
        return False

    def mouse_click_blank(self, coordinate=(1, 1), times=1, move_back=True) -> bool:
        """在空白位置点击鼠标
        Args:
            coordinate (tuple): 坐标元组 (x, y)
            times (int): 点击次数
            move_back (bool): 是否在点击后将鼠标移动回原位置
        Returns:
            bool (True) : 总是返回True表示操作执行完毕
        """
        if move_back:
            current_mouse_position = self.get_mouse_position()

        msg = "点击（1，1）空白位置"
        log.debug(msg, stacklevel=2)
        x = coordinate[0] + random.randint(0, 10)
        y = coordinate[1] + random.randint(0, 10)
        for i in range(times):
            self.set_mouse_pos(x, y)
            self.set_active()
            self.mouse_down(x, y)
            sleep(humanised_delay(0.05, "gaussian"))  # 模拟人类按下 and 松开时间间隔
            self.mouse_up(x, y)
            if times > 1 and i < times - 1:
                sleep(humanised_delay(0.1, "gaussian"))

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

        self.wait_pause()
        return True

    def mouse_drag_link(self, position: list, drag_time=0.1, move_back=True) -> None:
        """鼠标从指定位置拖动到指定位置
        Args:
            x (int): 起始x坐标
            y (int): 起始y坐标
            position (list): 目标位置列表
            drag_time (float): 拖动时间
        """
        if move_back:
            current_mouse_position = self.get_mouse_position()

        self.set_active()
        start_x, start_y = position[0][0], position[0][1]
        self._post_bezier_move(start_x, start_y)
        self.mouse_down(start_x, start_y)
        
        curr_x, curr_y = start_x, start_y
        hwnd = screen.handle.hwnd
        for pos in position:
            tx, ty = pos[0], pos[1]
            path = generate_bezier_path((curr_x, curr_y), (tx, ty))
            step_time = drag_time / max(1, len(path))
            for px, py in path:
                if self.driver:
                    self.driver.mouse_move(px, py)
                else:
                    long_position = win32api.MAKELONG(px, py)
                    wparam = win32con.MK_LBUTTON
                    if self.use_post_message:
                        win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, long_position)
                    else:
                        win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, long_position)
                sleep(humanised_delay(step_time, "gaussian"))
            curr_x, curr_y = tx, ty
            
        self.last_x = curr_x
        self.last_y = curr_y
        self.mouse_up(curr_x, curr_y)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def set_active(self):
        """将游戏窗口设置为输入焦点以让 Unity 接受输入事件"""
        hwnd = screen.handle.hwnd
        if hwnd:
            # 如果最小化则显示
            if screen.handle.isMinimized:
                screen.handle.set_window_transparent()
                screen.handle.restore()
                sleep(0.5)

            # 发送激活消息（但不改变Z序）
            if self.use_post_message:
                win32api.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
            else:
                win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        else:
            log.error("未初始化hwnd")

    def mouse_down(self, x, y):
        """鼠标左键按下
        Args:
            x (number): 相对于窗口左上角的 x 轴坐标
            y (number): 相对于窗口左上角的 y 轴坐标
        """
        if self.driver:
            self.driver.mouse_down(int(x), int(y))
            return
        x = int(x)
        y = int(y)
        hwnd = screen.handle.hwnd
        long_positon = win32api.MAKELONG(x, y)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, long_positon)
            sleep(0.02 + cfg.config.mouse_down_duration)
        else:
            win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, long_positon)
            sleep(0.01)

    def mouse_up(self, x, y):
        """鼠标左键抬起
        Args:
            x (number): 相对于窗口左上角的 x 轴坐标
            y (number): 相对于窗口左上角的 y 轴坐标
        """
        if self.driver:
            self.driver.mouse_up(int(x), int(y))
            return
        x = int(x)
        y = int(y)
        hwnd = screen.handle.hwnd
        long_positon = win32api.MAKELONG(x, y)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, long_positon)
            sleep(0.02)
        else:
            win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, long_positon)
            sleep(0.01)

    def set_mouse_pos(self, x, y, duration: float = 0):
        """移动光标位置
        Args:
            x (number): 相对于窗口左上角的 x 轴坐标
            y (number): 相对于窗口左上角的 y 轴坐标
        """
        x = int(x)
        y = int(y)
        rect = screen.handle.rect(True)
        if duration <= 0:
            self._mouse_move_to(rect[0] + x, rect[1] + y)
        else:
            self._mouse_move_to(rect[0] + x, rect[1] + y, duration=duration)

    def key_down(self, key: str):
        """键盘按键按下
        Args:
            key (str): 按键名称
        """
        if self.driver:
            self.driver.key_down(key)
            return
        hwnd = screen.handle.hwnd
        vk = key_list[key.lower()]
        wparam = self._make_key_wparam(vk)
        lparam = self._make_key_lparam(vk, key_up=False)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, wparam, lparam)
        else:
            win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, wparam, lparam)

    def key_up(self, key: str):
        """键盘按键抬起
        Args:
            key (str): 按键名称
        """
        if self.driver:
            self.driver.key_up(key)
            return
        hwnd = screen.handle.hwnd
        vk = key_list[key.lower()]
        wparam = self._make_key_wparam(vk)
        lparam = self._make_key_lparam(vk, key_up=True)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, wparam, lparam)
        else:
            win32api.SendMessage(hwnd, win32con.WM_KEYUP, wparam, lparam)

    def key_press(self, key):
        """一次键盘按键操作
        Args:
            key (str): 按键名称
        """
        self.set_active()
        self.key_down(key)
        sleep(humanised_delay(0.05, "gaussian"))
        self.key_up(key)

    def input_text(self, text: str):
        """将 `text` 通过 WM_CHAR 消息逐字符输入目标窗口（后台模式）。

        使用 WM_CHAR 消息而非 WM_SETTEXT，因为游戏窗口通常不处理 WM_SETTEXT。
        对每个字符发送单独 the WM_CHAR 消息。
        """
        if not text:
            log.warning("未提供要粘贴的文本")
            return
        hwnd = screen.handle.hwnd
        if not hwnd:
            log.warning("未获取窗口句柄")
            return
        try:
            # 对每个字符发送 WM_CHAR 消息
            for char in text:
                char_code = ord(char)
                # wParam: 字符代码（Unicode）
                # lParam: 重复计数和标志（为简化起见设为 0）
                if self.use_post_message:
                    win32api.PostMessage(hwnd, win32con.WM_CHAR, char_code, 0)
                else:
                    win32api.SendMessage(hwnd, win32con.WM_CHAR, char_code, 0)
                sleep(0.01)  # 字符之间的延迟，防止字符丢失
        except Exception as e:
            log.debug(f"通过 WM_CHAR 输入文本失败: {e}")

    def mouse_move(self, coordinate=(1, 1)) -> None:
        """鼠标移动到指定坐标

        Args:
            coordinate (tuple): 坐标元组 (x, y)
        """
        self._mouse_move_to(coordinate[0], coordinate[1])
        self.wait_pause()

    def _mouse_move_to(self, x, y, duration: float = 0):
        """将鼠标移动到指定位置（绝对于屏幕坐标）

        Args:
            x (int): x坐标
            y (int): y坐标
        """
        x = int(x)
        y = int(y)
        start_x, start_y = self.get_mouse_position()
        path = generate_bezier_path((start_x, start_y), (x, y))
        step_time = 0.01
        if duration > 0:
            step_time = duration / max(1, len(path))
        for px, py in path:
            if self.driver:
                self.driver.mouse_move(px, py)
            else:
                self._set_mouse_pos(px, py)
            sleep(humanised_delay(step_time, "gaussian"))

    def _set_mouse_pos(self, x: int, y: int):
        """将鼠标移动到指定位置（绝对于屏幕坐标）

        Args:
            x (int): x坐标
            y (int): y坐标
        """
        if self.driver:
            self.driver.mouse_move(x, y)
            return
        try:
            win32api.SetCursorPos((x, y))
        except PyWinTypesError as e:
            # 奇怪的权限冲突 (183:当文件已存在时，无法创建该文件。)
            # 偶尔出现不影响使用

            log.debug(f"鼠标移动失败: {e}")
            try:
                pyautogui.moveTo(x, y)
            except Exception as e:
                log.error(f"鼠标移动失败: {type(e)}: {e}")


class WindowMoveInput(WinAbstractInput, metaclass=SingletonMeta):
    """基于移动窗口位置改变光标相对位置的输入方式"""

    def mouse_to_blank(self, coordinate=(1, 1), move_back=False) -> None:
        # FIXME: 移动窗口来防止遮蔽不是一个好选择
        return

    def mouse_scroll(self, direction: int = 120) -> bool:
        return False

    def mouse_drag(self, x, y, drag_time=0.1, dx=0, dy=0, move_back=True) -> None:
        pos = self._set_window_pos(x, y)
        self.set_active()
        self.mouse_down(x, y)
        self._window_move_to(x + dx, y + dy, duration=drag_time)
        # 注入随机拖拽延迟
        sleep(humanised_delay(drag_time * 0.3 if drag_time * 0.3 > 0.2 else 0.2, "gaussian"))
        self.mouse_up(x + dx, y + dy)
        screen.handle.set_window_pos(*pos)

    def mouse_drag_down(self, x, y, reverse=1, move_back=True) -> None:
        scale = cfg.set_win_size / 1080
        self.set_active()
        pos = self._set_window_pos(x, y)
        self.mouse_down(x, y)
        end_y = y + int(500 * scale * reverse)
        self._window_move_to(x, end_y, duration=0.6)
        self.mouse_up(x, end_y)

        screen.handle.set_window_pos(*pos)

    def mouse_drag_link(self, position: list, drag_time=0.1, move_back=False) -> None:
        raw_pos = self._set_window_pos(position[0][0], position[0][1])
        self.set_active()
        self.mouse_down(position[0][0], position[0][1])
        for pos in position:
            self._window_move_to(pos[0], pos[1], duration=drag_time)

        self.mouse_up(position[-1][0], position[-1][1])
        screen.handle.set_window_pos(*raw_pos)

    def mouse_click_blank(self, coordinate=(1, 1), times=1, move_back=False) -> bool:
        msg = "点击（1，1）空白位置"
        log.debug(msg, stacklevel=2)
        x = coordinate[0] + random.randint(0, 10)
        y = coordinate[1] + random.randint(0, 10)
        self.mouse_click(x, y, times=times)
        return True

    def _window_move_to(
        self, x_or_pos: int | tuple[int, int], y: int = -32000, duration: float = 0
    ) -> tuple[int, int]:
        if duration <= 0:
            return self._set_window_pos(x_or_pos, y)
        else:
            if isinstance(x_or_pos, tuple):
                target_x, target_y = x_or_pos
            else:
                target_x = x_or_pos
                target_y = y
        raw_pos = screen.handle.rect()[:2]
        current_x, current_y = screen.handle.mouse_pos_to_client_mouse(
            *self.get_mouse_position()
        )
        path = generate_bezier_path((current_x, current_y), (target_x, target_y))
        step_time = duration / max(1, len(path))
        for px, py in path:
            self._set_window_pos(px, py)
            sleep(humanised_delay(step_time, "gaussian"))

        self._set_window_pos(target_x, target_y)
        return raw_pos

    @overload
    def _set_window_pos(self, x_or_pos: int, y: int) -> tuple[int, int]: ...
    @overload
    def _set_window_pos(self, x_or_pos: tuple[int, int]) -> tuple[int, int]: ...
    def _set_window_pos(
        self,
        x_or_pos: int | tuple[int, int],
        y: int = -32000,
    ) -> tuple[int, int]:
        """将窗口基于工作区左上角的指定位置移动到鼠标当前位置"""
        hwnd = screen.handle.hwnd
        if isinstance(x_or_pos, tuple):
            x, y = x_or_pos
        else:
            x = x_or_pos
        if screen.handle.isMinimized:
            screen.handle.set_window_transparent()
            screen.handle.restore()
            sleep(0.1)  # 先恢复窗口,防止被放在左上角
        original_rect = screen.handle.rect()
        mouse_pos = self.get_mouse_position()
        x = int(x)
        y = int(y)

        if cfg.set_win_position == "free":
            dx, dy = screen.handle.client_to_window(0, 0)
        else:
            dx = 0
            dy = 0

        if self.driver:
            self.driver.mouse_move(mouse_pos[0] + x, mouse_pos[1] + y)
        else:
            win32gui.SetWindowPos(
                hwnd,
                None,
                mouse_pos[0] - x + dx,
                mouse_pos[1] - y + dy,
                0,
                0,
                win32con.SWP_NOSIZE
                | win32con.SWP_NOZORDER
                | win32con.SWP_NOACTIVATE
                | win32con.SWP_NOSENDCHANGING
                | win32con.SWP_NOREDRAW,
            )

        return original_rect[:2]

    def set_active(self):
        """将游戏窗口设置为输入焦点以让 Unity 接受输入事件"""
        hwnd = screen.handle.hwnd
        if hwnd:
            # 如果最小化则显示
            if screen.handle.isMinimized:
                screen.handle.set_window_transparent()
                screen.handle.restore()
                sleep(0.5)

            # 发送激活消息（但不改变Z序）
            if self.use_post_message:
                win32api.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
            else:
                win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        else:
            log.error("未初始化hwnd")

    def key_down(self, key: str):
        """键盘按键按下
        Args:
            key (str): 按键名称
        """
        if self.driver:
            self.driver.key_down(key)
            return
        hwnd = screen.handle.hwnd
        vk = key_list[key.lower()]
        wparam = self._make_key_wparam(vk)
        lparam = self._make_key_lparam(vk, key_up=False)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, wparam, lparam)
        else:
            win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, wparam, lparam)

    def key_up(self, key: str):
        """键盘按键抬起
        Args:
            key (str): 按键名称
        """
        if self.driver:
            self.driver.key_up(key)
            return
        hwnd = screen.handle.hwnd
        vk = key_list[key.lower()]
        wparam = self._make_key_wparam(vk)
        lparam = self._make_key_lparam(vk, key_up=True)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, wparam, lparam)
        else:
            win32api.SendMessage(hwnd, win32con.WM_KEYUP, wparam, lparam)

    def key_press(self, key):
        """一次键盘按键操作
        Args:
            key (str): 按键名称
        """
        self.set_active()
        self.key_down(key)
        sleep(humanised_delay(0.05, "gaussian"))
        self.key_up(key)

    def input_text(self, text: str):
        """将 `text` 通过 WM_CHAR 消息逐字符输入窗口。

        使用 WM_CHAR 消息而非 WM_SETTEXT，因为游戏窗口通常不处理 WM_SETTEXT。
        对每个字符发送单独的 WM_CHAR 消息。
        """
        if not text:
            log.warning("未提供要粘贴的文本")
            return
        hwnd = screen.handle.hwnd
        if not hwnd:
            log.warning("未获取窗口句柄")
            return
        try:
            # 对每个字符发送 WM_CHAR 消息
            for char in text:
                char_code = ord(char)
                # wParam: 字符代码（Unicode）
                # lParam: 重复计数和标志（为简化起见设为 0）
                if self.use_post_message:
                    win32api.PostMessage(hwnd, win32con.WM_CHAR, char_code, 0)
                else:
                    win32api.SendMessage(hwnd, win32con.WM_CHAR, char_code, 0)
                sleep(0.01)  # 字符之间的延迟，防止字符丢失
        except Exception as e:
            log.debug(f"通过 WM_CHAR 输入文本失败: {e}")

    def mouse_down(self, x, y):
        """鼠标左键按下
        Args:
            x (number): 相对于窗口左上角的 x 轴坐标
            y (number): 相对于窗口左上角的 y 轴坐标
        """
        if self.driver:
            self.driver.mouse_down(int(x), int(y))
            return
        x = int(x)
        y = int(y)
        hwnd = screen.handle.hwnd
        long_positon = win32api.MAKELONG(x, y)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, long_positon)
            sleep(0.02 + cfg.config.mouse_down_duration)
        else:
            win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, long_positon)
            sleep(0.01)

    def mouse_up(self, x, y):
        """鼠标左键抬起
        Args:
            x (number): 相对于窗口左上角的 x 轴坐标
            y (number): 相对于窗口左上角的 y 轴坐标
        """
        if self.driver:
            self.driver.mouse_up(int(x), int(y))
            return
        x = int(x)
        y = int(y)
        hwnd = screen.handle.hwnd
        long_positon = win32api.MAKELONG(x, y)
        if self.use_post_message:
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, long_positon)
            sleep(0.02)
        else:
            win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, long_positon)
            sleep(0.01)

    def mouse_click(self, x, y, times=1, move_back=False) -> bool:
        msg = f"点击位置:({x},{y})"
        log.debug(msg, stacklevel=2)
        pos = None
        for _ in range(times):
            if not pos:
                pos = self._set_window_pos(x, y)
            else:
                self._set_window_pos(x, y)
            self.set_active()
            self.mouse_down(x, y)
            sleep(humanised_delay(0.05, "gaussian"))
            self.mouse_up(x, y)
        assert pos is not None
        screen.handle.set_window_pos(*pos)
        self.wait_pause()
        return True
