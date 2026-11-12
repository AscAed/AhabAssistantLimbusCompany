import ctypes
from contextlib import contextmanager
from dataclasses import dataclass
from time import monotonic, sleep
from typing import Callable, overload

import pyautogui
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

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120


class _MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouse_data", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("extra_info", ctypes.c_void_p),
    ]


class _InputUnion(ctypes.Union):
    _fields_ = [("mouse", _MouseInput)]


class _Input(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", ctypes.c_ulong), ("union", _InputUnion)]


class _LastInputInfo(ctypes.Structure):
    _fields_ = [("cb_size", ctypes.c_uint), ("dw_time", ctypes.c_uint)]


@dataclass(frozen=True)
class _MouseLease:
    game_hwnd: int
    original_foreground: int
    original_position: tuple[int, int]
    original_cursor: tuple[int, int]
    was_paused: bool

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

    def _randomize_coords(self, x: int, y: int, radius: int = 4) -> tuple[int, int]:
        """Return coordinates unchanged for deterministic, audit-safe input behavior."""
        return x, y



def human_delay(base_time=0.1, std_dev=0.03):
    """生成固定延迟，保持接口兼容，下限保护为0.01。"""
    return max(0.01, base_time)


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

    def mouse_scroll(self, direction: int = -3, x: int = None, y: int = None) -> bool:
        if direction <= 0:
            msg = "鼠标滚动滚轮，远离界面"
        else:
            msg = "鼠标滚动滚轮，拉近界面"
        log.debug(msg, stacklevel=2)
        if x is not None and y is not None:
            self.mouse_move((x, y))
        pyautogui.scroll(direction)
        return True

    def mouse_click_blank(self, coordinate=(1, 1), times=1, move_back=False) -> bool:
        if move_back:
            current_mouse_position = self.get_mouse_position()

        msg = "点击（1，1）空白位置"
        log.debug(msg, stacklevel=2)
        x = coordinate[0] + 5
        y = coordinate[1] + 5
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
        target_pos = (int(coordinate[0]), int(coordinate[1]))
        if self.driver:
            start_pos = self.get_mouse_position()
            path = generate_bezier_path(start_pos, target_pos, steps=12)
            for px, py in path:
                self.driver.mouse_move(px, py)
        else:
            # pyautogui's zero-duration move is synchronous and avoids a fixed
            # per-point delay that made every long move visibly stutter.
            pyautogui.moveTo(*target_pos)
        self.wait_pause()

    def mouse_drag_link(
        self,
        position: list,
        drag_time=0.1,
        move_back=False,
        resolve_last_position: Callable[[], tuple[int, int] | list[int] | None] | None = None,
    ) -> None:
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

        if resolve_last_position is not None:
            resolved = resolve_last_position()
            if resolved is not None:
                tx, ty = self.pos_offset(resolved[0], resolved[1])
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

    def mouse_click(self, x, y, times=1, move_back=False) -> bool:
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

        rx, ry = self._randomize_coords(x, y)
        msg = f"点击位置:({x},{y}) -> 随机偏移后:({rx},{ry})"
        log.debug(msg, stacklevel=2)
        for i in range(times):
            self.set_mouse_pos(rx, ry)
            self.set_active()
            self.mouse_down(rx, ry)
            sleep(humanised_delay(0.05, "gaussian"))  # 模拟人类按下和松开的时间间隔
            self.mouse_up(rx, ry)
            if times > 1 and i < times - 1:
                rx, ry = self._randomize_coords(x, y)
                sleep(humanised_delay(0.1, "gaussian"))

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

        self.wait_pause()

        return True

    def mouse_drag_down(self, x, y, reverse=1, move_back=False) -> None:
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
        rx, ry = self._randomize_coords(x, y)
        
        is_active = screen.handle.isActive
        client_rect = screen.handle.rect() if is_active else None

        if is_active and client_rect:
            win32api.SetCursorPos((client_rect[0] + rx, client_rect[1] + ry))
        
        self._post_bezier_move(rx, ry)
        self.mouse_down(rx, ry)
        end_y = ry + int(300 * scale * reverse)
        
        path = generate_bezier_path((rx, ry), (rx, end_y))
        hwnd = screen.handle.hwnd
        step_time = 0.4 / max(1, len(path))
        for px, py in path:
            if is_active and client_rect:
                win32api.SetCursorPos((client_rect[0] + px, client_rect[1] + py))
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
            
        self.last_x = rx
        self.last_y = end_y
        
        if is_active and client_rect:
            win32api.SetCursorPos((client_rect[0] + rx, client_rect[1] + end_y))
        self.mouse_up(rx, end_y)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def mouse_drag(self, x, y, drag_time=0.1, dx=0, dy=0, move_back=False) -> None:
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
        rx, ry = self._randomize_coords(x, y)
        
        is_active = screen.handle.isActive
        client_rect = screen.handle.rect() if is_active else None

        if is_active and client_rect:
            win32api.SetCursorPos((client_rect[0] + rx, client_rect[1] + ry))
            
        self._post_bezier_move(rx, ry)
        self.mouse_down(rx, ry)

        end_x, end_y = int(round(rx + dx)), int(round(ry + dy))
        path = generate_bezier_path((rx, ry), (end_x, end_y))
        hwnd = screen.handle.hwnd
        step_time = drag_time / max(1, len(path))
        for px, py in path:
            if is_active and client_rect:
                win32api.SetCursorPos((client_rect[0] + px, client_rect[1] + py))
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

        self.last_x = end_x
        self.last_y = end_y
        # 注入随机拖拽延迟
        sleep(humanised_delay(drag_time * 0.3 if drag_time * 0.3 > 0.2 else 0.2, "gaussian"))
        
        if is_active and client_rect:
            win32api.SetCursorPos((client_rect[0] + end_x, client_rect[1] + end_y))
        self.mouse_up(end_x, end_y)

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

    def mouse_scroll(self, direction: int = -3, x: int = None, y: int = None) -> bool:
        """
        在后台进行鼠标滚动操作
        Args:
            direction (int): 滚动方向，正值表示拉近，负值表示缩小
            x (int): 滚动坐标 x，如果为 None 则默认居中
            y (int): 滚动坐标 y，如果为 None 则默认居中
        Returns:
            bool (True) : 表示支持该操作
        """
        hwnd = screen.handle.hwnd
        if hwnd:
            delta = direction * 120
            # 保留有符号整数，避免在 64 位系统下掩码截断导致负滚动量被错误解释为正值
            wparam = delta << 16
            
            # 如果未指定坐标，发送到窗口中央以防坐标错误，并且确保游戏聚焦
            if x is None or y is None:
                h = cfg.set_win_size
                w = int(h * 16 / 9)
                cx, cy = w // 2, h // 2
            else:
                cx, cy = x, y

            import win32gui
            screen_x, screen_y = win32gui.ClientToScreen(hwnd, (cx, cy))
            lparam = win32api.MAKELONG(screen_x, screen_y)
            self._mouse_move_to(screen_x, screen_y)

            # 动态寻找真正包含该坐标的子窗口（例如 Qt5QWindowIcon 或 QtRenderWindow），直接向其投递滚动消息。
            # 必须验证找到的句柄是游戏窗口 hwnd 的子窗口，否则当游戏在后台时，坐标处可能是其他前台窗口（如控制台），
            # 导致滚轮消息投递到错误目标。
            found_hwnd = win32gui.WindowFromPoint((screen_x, screen_y))
            target_hwnd = hwnd
            is_valid_child = False
            if found_hwnd and found_hwnd != hwnd:
                temp = found_hwnd
                while temp:
                    parent = win32gui.GetParent(temp)
                    if parent == hwnd:
                        target_hwnd = found_hwnd
                        is_valid_child = True
                        break
                    temp = parent

            # 如果在后台模式下被前台窗口遮挡，WindowFromPoint 会返回外部窗口。
            # 此时我们通过程序遍历寻找游戏窗口真正的渲染子窗口（EnumChildWindows），避免退化至 root hwnd 导致消息被 Unity 丢弃。
            if not is_valid_child:
                child_hwnds = []
                def enum_child_callback(child_hwnd, param):
                    child_hwnds.append(child_hwnd)
                    return True
                win32gui.EnumChildWindows(hwnd, enum_child_callback, None)
                if child_hwnds:
                    target_hwnd = child_hwnds[0]

            # 激活窗口并发送焦点消息，确保 Unity 引擎处于可接收输入的状态，
            # 否则后台模式下 WM_MOUSEWHEEL 会被 Unity 丢弃。
            self.set_active()
            win32api.PostMessage(target_hwnd, win32con.WM_SETFOCUS, 0, 0)
            win32api.PostMessage(target_hwnd, win32con.WM_MOUSEWHEEL, wparam, lparam)
            sleep(0.3)
            return True
        return False

    def mouse_click_blank(self, coordinate=(1, 1), times=1, move_back=False) -> bool:
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
        x = coordinate[0] + 5
        y = coordinate[1] + 5
        rx, ry = self._randomize_coords(x, y)
        for i in range(times):
            self.set_mouse_pos(rx, ry)
            self.set_active()
            self.mouse_down(rx, ry)
            sleep(humanised_delay(0.05, "gaussian"))  # 模拟人类按下 and 松开时间间隔
            self.mouse_up(rx, ry)
            if times > 1 and i < times - 1:
                rx, ry = self._randomize_coords(x, y)
                sleep(humanised_delay(0.1, "gaussian"))

        if move_back and current_mouse_position:
            self.mouse_move(current_mouse_position)

        self.wait_pause()
        return True

    def mouse_drag_link(
        self,
        position: list,
        drag_time=0.1,
        move_back=False,
        resolve_last_position: Callable[[], tuple[int, int] | list[int] | None] | None = None,
    ) -> None:
        """鼠标从指定位置拖动到指定位置
        Args:
            x (int): 起始x坐标
            y (int): 起始y坐标
            position (list): 目标位置列表
            drag_time (float): 拖动时间
        """
        if move_back:
            current_mouse_position = self.get_mouse_position()

        mouse_pressed = False
        curr_x = curr_y = 0
        is_active = False
        client_rect = None
        try:
            self.set_active()
            start_x, start_y = self._randomize_coords(position[0][0], position[0][1])
            curr_x, curr_y = start_x, start_y
            is_active = screen.handle.isActive
            client_rect = screen.handle.rect() if is_active else None
            if is_active and client_rect:
                win32api.SetCursorPos((client_rect[0] + start_x, client_rect[1] + start_y))
            log.debug(f"后台连线开始，按下位置:({start_x},{start_y})")
            self._post_bezier_move(start_x, start_y)
            # Mark pressed before dispatch: a partially delivered down message still needs an up.
            mouse_pressed = True
            self.mouse_down(start_x, start_y)

            hwnd = screen.handle.hwnd
            for pos in position:
                tx, ty = pos[0], pos[1]
                path = generate_bezier_path((curr_x, curr_y), (tx, ty))
                step_time = drag_time / max(1, len(path))
                for px, py in path:
                    curr_x, curr_y = px, py
                    if is_active and client_rect:
                        win32api.SetCursorPos((client_rect[0] + px, client_rect[1] + py))
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

            if resolve_last_position is not None:
                resolved = resolve_last_position()
                if resolved is not None:
                    tx, ty = int(resolved[0]), int(resolved[1])
                    path = generate_bezier_path((curr_x, curr_y), (tx, ty))
                    step_time = drag_time / max(1, len(path))
                    for px, py in path:
                        curr_x, curr_y = px, py
                        if is_active and client_rect:
                            win32api.SetCursorPos((client_rect[0] + px, client_rect[1] + py))
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
        finally:
            if mouse_pressed:
                self.last_x = curr_x
                self.last_y = curr_y
                if is_active and client_rect:
                    win32api.SetCursorPos((client_rect[0] + curr_x, client_rect[1] + curr_y))
                log.debug(f"后台连线结束，释放位置:({curr_x},{curr_y})")
                self.mouse_up(curr_x, curr_y)

            if move_back and current_mouse_position:
                self.mouse_move(current_mouse_position)

    def set_active(self):
        """将游戏窗口激活并置前，确保输入坐标与游戏接收的坐标一致"""
        hwnd = screen.handle.hwnd
        if hwnd:
            # 如果最小化则显示
            if screen.handle.isMinimized:
                screen.handle.set_window_transparent()
                screen.handle.restore()
                sleep(0.5)

            # 置于前台，确保 cursor 坐标与 Unity 的坐标一致（闲置环境下无需考虑占用问题）
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                log.debug(f"SetForegroundWindow failed: {e}")

            # 发送激活消息
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
    """后台模式输入：移动游戏窗口，并为 Unity 建立短暂的输入焦点租约。"""

    USER_IDLE_REQUIRED_MS = 500
    USER_IDLE_TIMEOUT_SECONDS = 10.0
    FOCUS_ACQUIRE_TIMEOUT_SECONDS = 0.5
    INPUT_SETTLE_MS = 50  # Unity input event processing time

    def mouse_to_blank(self, coordinate=(1, 1), move_back=False) -> None:
        # FIXME: 移动窗口来防止遮蔽不是一个好选择
        return

    def _send_mouse_input(self, flags: int, mouse_data: int = 0) -> bool:
        operation = {
            MOUSEEVENTF_MOVE: "move",
            MOUSEEVENTF_LEFTDOWN: "left_down",
            MOUSEEVENTF_LEFTUP: "left_up",
            MOUSEEVENTF_WHEEL: "wheel",
        }.get(flags, f"flags_{flags}")
        event = _Input(
            type=INPUT_MOUSE,
            mouse=_MouseInput(
                dx=0,
                dy=0,
                mouse_data=mouse_data,
                flags=flags,
                time=0,
                extra_info=None,
            ),
        )
        sent = ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(_Input))
        success = sent == 1
        log.debug(
            "后台 SendInput: operation=%s flags=%s mouse_data=%s sent=%s success=%s",
            operation,
            flags,
            mouse_data,
            sent,
            success,
        )
        return success

    @staticmethod
    def _get_last_input_elapsed_ms() -> int | None:
        info = _LastInputInfo(cb_size=ctypes.sizeof(_LastInputInfo))
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        tick = ctypes.windll.kernel32.GetTickCount()
        return max(0, int(tick - info.dw_time))

    def _wait_for_user_idle(self) -> bool:
        log.debug(
            "lease_wait_start: required_ms=%s timeout_s=%s",
            self.USER_IDLE_REQUIRED_MS,
            self.USER_IDLE_TIMEOUT_SECONDS,
        )
        deadline = monotonic() + self.USER_IDLE_TIMEOUT_SECONDS
        while monotonic() < deadline:
            if self.is_pause:
                self.wait_pause()
            elapsed = self._get_last_input_elapsed_ms()
            if elapsed is not None and elapsed >= self.USER_IDLE_REQUIRED_MS:
                # Give Unity time to process input events before restoring foreground
                sleep(self.INPUT_SETTLE_MS / 1000.0)
                return True
            sleep(0.05)
        log.warning("后台输入等待用户空闲超时: timeout=%ss", self.USER_IDLE_TIMEOUT_SECONDS)
        return False

    def _activate_for_lease(self, hwnd: int) -> bool:
        # Windows may reject cross-process activation while another thread owns
        # the foreground lock. Temporarily attach input queues for this single
        # transaction, then detach immediately after the activation attempt.
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as exc:
            log.warning("后台输入焦点租约获取失败: hwnd=%s error=%s", hwnd, exc)
            return False

        deadline = monotonic() + self.FOCUS_ACQUIRE_TIMEOUT_SECONDS
        while monotonic() < deadline:
            if win32gui.GetForegroundWindow() == hwnd:
                return True
            sleep(0.01)

        try:
            user32 = ctypes.windll.user32
            foreground = int(user32.GetForegroundWindow())
            target_thread = int(user32.GetWindowThreadProcessId(hwnd, None))
            foreground_thread = int(user32.GetWindowThreadProcessId(foreground, None)) if foreground else 0
            current_thread = int(user32.GetCurrentThreadId())
            attached = bool(
                foreground_thread
                and foreground_thread != current_thread
                and foreground_thread != target_thread
                and user32.AttachThreadInput(current_thread, foreground_thread, True)
            )
            try:
                win32gui.SetForegroundWindow(hwnd)
                if target_thread != current_thread:
                    user32.AttachThreadInput(current_thread, target_thread, True)
                deadline = monotonic() + self.FOCUS_ACQUIRE_TIMEOUT_SECONDS
                while monotonic() < deadline:
                    if win32gui.GetForegroundWindow() == hwnd:
                        return True
                    sleep(0.01)
            finally:
                if target_thread != current_thread:
                    user32.AttachThreadInput(current_thread, target_thread, False)
                if attached:
                    user32.AttachThreadInput(current_thread, foreground_thread, False)
        except Exception as exc:
            log.debug("后台输入焦点租约附加线程尝试失败: hwnd=%s error=%s", hwnd, exc)
        log.warning("后台输入焦点租约验证失败: hwnd=%s", hwnd)
        return False

    def _restore_foreground(self, hwnd: int) -> bool:
        if not hwnd:
            return True
        try:
            if not win32gui.IsWindow(hwnd):
                log.warning("后台输入恢复原前台窗口失败：句柄已失效 hwnd=%s", hwnd)
                return False
            win32gui.SetForegroundWindow(hwnd)
        except Exception as exc:
            log.warning("后台输入恢复原前台窗口失败: hwnd=%s error=%s", hwnd, exc)
            return False

        deadline = monotonic() + self.FOCUS_ACQUIRE_TIMEOUT_SECONDS
        while monotonic() < deadline:
            if win32gui.GetForegroundWindow() == hwnd:
                return True
            sleep(0.01)

        # The worker thread may not own the foreground lock. Attach only for
        # this bounded restoration attempt, then detach before returning.
        try:
            user32 = ctypes.windll.user32
            current_thread = int(user32.GetCurrentThreadId())
            target_thread = int(user32.GetWindowThreadProcessId(hwnd, None))
            foreground = int(user32.GetForegroundWindow())
            foreground_thread = int(user32.GetWindowThreadProcessId(foreground, None)) if foreground else 0
            attached_foreground = bool(
                foreground_thread
                and foreground_thread != current_thread
                and foreground_thread != target_thread
                and user32.AttachThreadInput(current_thread, foreground_thread, True)
            )
            attached_target = False
            try:
                if target_thread != current_thread:
                    attached_target = bool(user32.AttachThreadInput(current_thread, target_thread, True))
                win32gui.SetForegroundWindow(hwnd)
                deadline = monotonic() + self.FOCUS_ACQUIRE_TIMEOUT_SECONDS
                while monotonic() < deadline:
                    if win32gui.GetForegroundWindow() == hwnd:
                        return True
                    sleep(0.01)
            finally:
                if attached_target:
                    user32.AttachThreadInput(current_thread, target_thread, False)
                if attached_foreground:
                    user32.AttachThreadInput(current_thread, foreground_thread, False)
        except Exception as exc:
            log.debug("后台输入恢复前台附加线程尝试失败: hwnd=%s error=%s", hwnd, exc)
        log.warning("后台输入恢复原前台窗口未通过验证: hwnd=%s", hwnd)
        return False

    def _begin_mouse_lease(self, x: int, y: int) -> _MouseLease | None:
        game_hwnd = screen.handle.hwnd
        if not game_hwnd:
            log.warning("后台输入无法建立焦点租约：游戏窗口句柄为空")
            return None
        original_foreground = win32gui.GetForegroundWindow()
        original_cursor = tuple(self.get_mouse_position())
        was_paused = bool(self.is_pause)
        if not self._wait_for_user_idle():
            return None

        original_position = self._set_window_pos(int(x), int(y))
        if not self._activate_for_lease(game_hwnd):
            try:
                self._restore_window_position(original_position)
            finally:
                self._restore_foreground(original_foreground)
            return None
        log.debug(
            "lease_acquired: game_hwnd=%s original_foreground=%s cursor=%s paused=%s",
            game_hwnd,
            original_foreground,
            original_cursor,
            was_paused,
        )
        return _MouseLease(
            game_hwnd,
            original_foreground,
            original_position,
            original_cursor,
            was_paused,
        )

    def _restore_window_position(self, position: tuple[int, int]) -> bool:
        hwnd = screen.handle.hwnd
        if not hwnd or not win32gui.IsWindow(hwnd):
            log.warning("后台输入恢复游戏窗口失败：句柄无效 hwnd=%s", hwnd)
            return False
        try:
            win32gui.SetWindowPos(
                hwnd,
                None,
                int(position[0]),
                int(position[1]),
                0,
                0,
                win32con.SWP_NOSIZE
                | win32con.SWP_NOZORDER
                | win32con.SWP_NOACTIVATE
                | win32con.SWP_NOSENDCHANGING,
            )
            restored = tuple(screen.handle.rect()[:2]) == tuple(position)
        except Exception as exc:
            log.warning("后台输入恢复游戏窗口位置失败: error=%s", exc)
            return False
        if not restored:
            log.warning("后台输入恢复游戏窗口位置校验失败: expected=%s", position)
        return restored

    def _end_mouse_lease(self, lease: _MouseLease) -> bool:
        restored = True
        restored = self._restore_window_position(lease.original_position)
        restored = self._restore_foreground(lease.original_foreground) and restored
        log.debug(
            "lease_released: game_hwnd=%s original_foreground=%s cursor=%s paused=%s restored=%s",
            lease.game_hwnd,
            lease.original_foreground,
            lease.original_cursor,
            lease.was_paused,
            restored,
        )
        return restored

    @contextmanager
    def _mouse_lease(self, x: int, y: int):
        lease = self._begin_mouse_lease(x, y)
        operation_error = None
        try:
            yield lease
        except BaseException as exc:
            operation_error = exc
            raise
        finally:
            if lease is not None:
                if not self._end_mouse_lease(lease):
                    restore_error = RuntimeError("后台输入租约释放失败，窗口或前台恢复未通过验证")
                    if operation_error is None:
                        raise restore_error
                    log.error("后台输入租约释放失败，保留原始操作异常: %s", operation_error)

    def _mouse_move_heartbeat(self) -> bool:
        return self._send_mouse_input(MOUSEEVENTF_MOVE)

    def mouse_scroll(self, direction: int = -3, x: int = None, y: int = None) -> bool:
        if x is None or y is None:
            height = cfg.set_win_size
            x, y = int(height * 16 / 9) // 2, height // 2

        with self._mouse_lease(int(x), int(y)) as lease:
            if lease is None:
                return False
            if not self._mouse_move_heartbeat():
                log.warning("后台滚轮鼠标位置心跳投递失败: game=%s", lease.game_hwnd)
                return False
            if not self._send_mouse_input(MOUSEEVENTF_WHEEL, int(direction * WHEEL_DELTA)):
                log.warning(
                    "后台滚轮 SendInput 失败: game=%s direction=%s",
                    lease.game_hwnd,
                    direction,
                )
                return False
            log.debug(
                "后台滚轮已通过焦点租约投递: game=%s direction=%s",
                lease.game_hwnd,
                direction,
            )
            # Give Unity time to process wheel events
            sleep(self.INPUT_SETTLE_MS / 1000.0)
            return True


    def batch_mouse_scroll(self, direction: int = -3, count: int = 1, x: int = None, y: int = None) -> bool:
        """在单个焦点租约内发送多个滚轮事件，提高效率。"""
        if x is None or y is None:
            height = cfg.set_win_size
            x, y = int(height * 16 / 9) // 2, height // 2

        with self._mouse_lease(int(x), int(y)) as lease:
            if lease is None:
                return False
            if not self._mouse_move_heartbeat():
                log.warning("后台批量滚轮鼠标位置心跳失败: game=%s", lease.game_hwnd)
                return False
            
            # Send multiple wheel events in the same lease
            for i in range(count):
                if not self._send_mouse_input(MOUSEEVENTF_WHEEL, int(direction * WHEEL_DELTA)):
                    log.warning(
                        "后台批量滚轮 SendInput 失败: game=%s direction=%s index=%s/%s",
                        lease.game_hwnd,
                        direction,
                        i+1,
                        count,
                    )
                    return False
                # Small delay between wheel events for Unity to process
                if i < count - 1:
                    sleep(0.01)
            
            log.debug(
                "后台批量滚轮已通过焦点租约投递: game=%s direction=%s count=%s",
                lease.game_hwnd,
                direction,
                count,
            )
            # Give Unity time to process all wheel events
            sleep(self.INPUT_SETTLE_MS / 1000.0)
            return True


    def mouse_drag(self, x, y, drag_time=0.1, dx=0, dy=0, move_back=True) -> bool:
        rx, ry = self._randomize_coords(x, y)
        with self._mouse_lease(rx, ry) as lease:
            if lease is None:
                return False
            pressed = False
            try:
                if not self._mouse_move_heartbeat():
                    log.warning("后台拖拽鼠标位置心跳失败: game=%s", lease.game_hwnd)
                    return False
                if not self._send_mouse_input(MOUSEEVENTF_LEFTDOWN):
                    log.warning("后台拖拽按下失败: game=%s", lease.game_hwnd)
                    return False
                pressed = True
                if not self._window_move_to(rx + dx, ry + dy, duration=drag_time):
                    log.warning("后台拖拽窗口移动失败")
                    return False
                if not self._mouse_move_heartbeat():
                    log.warning("后台拖拽移动心跳失败: game=%s", lease.game_hwnd)
                    return False
                sleep(humanised_delay(drag_time))
                if not self._send_mouse_input(MOUSEEVENTF_LEFTUP):
                    log.warning("后台拖拽抬起失败: game=%s", lease.game_hwnd)
                    return False
                pressed = False
                return True
            finally:
                if pressed:
                    self._send_mouse_input(MOUSEEVENTF_LEFTUP)

    def mouse_drag_down(self, x, y, reverse=1, move_back=True) -> bool:
        scale = cfg.set_win_size / 1080
        rx, ry = self._randomize_coords(x, y)
        with self._mouse_lease(rx, ry) as lease:
            if lease is None:
                return False
            pressed = False
            try:
                if not self._mouse_move_heartbeat():
                    log.warning("后台向下拖拽鼠标位置心跳失败: game=%s", lease.game_hwnd)
                    return False
                if not self._send_mouse_input(MOUSEEVENTF_LEFTDOWN):
                    log.warning("后台向下拖拽按下失败: game=%s", lease.game_hwnd)
                    return False
                pressed = True
                end_y = ry + int(500 * scale * reverse)
                if not self._window_move_to(rx, end_y, duration=0.6):
                    log.warning("后台向下拖拽窗口移动失败")
                    return False
                if not self._mouse_move_heartbeat():
                    log.warning("后台向下拖拽移动心跳失败: game=%s", lease.game_hwnd)
                    return False
                if not self._send_mouse_input(MOUSEEVENTF_LEFTUP):
                    log.warning("后台向下拖拽抬起失败: game=%s", lease.game_hwnd)
                    return False
                pressed = False
                return True
            finally:
                if pressed:
                    self._send_mouse_input(MOUSEEVENTF_LEFTUP)

    def mouse_drag_link(
        self,
        position: list,
        drag_time=0.1,
        move_back=False,
        resolve_last_position: Callable[[], tuple[int, int] | list[int] | None] | None = None,
    ) -> bool:
        start_x, start_y = self._randomize_coords(position[0][0], position[0][1])
        with self._mouse_lease(start_x, start_y) as lease:
            if lease is None:
                return False
            pressed = False
            try:
                if not self._mouse_move_heartbeat():
                    log.warning("后台连线鼠标位置心跳失败: game=%s", lease.game_hwnd)
                    return False
                if not self._send_mouse_input(MOUSEEVENTF_LEFTDOWN):
                    log.warning("后台连线按下失败: game=%s", lease.game_hwnd)
                    return False
                pressed = True
                for pos in position:
                    tx, ty = self._randomize_coords(pos[0], pos[1])
                    if not self._window_move_to(tx, ty, duration=drag_time):
                        log.warning("后台连线窗口移动失败")
                        return False
                    if not self._mouse_move_heartbeat():
                        log.warning("后台连线移动心跳失败: game=%s", lease.game_hwnd)
                        return False

                last = resolve_last_position() if resolve_last_position is not None else position[-1]
                if last is None:
                    last = position[-1]
                last_x, last_y = self._randomize_coords(last[0], last[1])
                if not self._window_move_to(last_x, last_y, duration=drag_time):
                    log.warning("后台连线末端窗口移动失败")
                    return False
                if not self._mouse_move_heartbeat():
                    log.warning("后台连线末端移动心跳失败: game=%s", lease.game_hwnd)
                    return False
                if not self._send_mouse_input(MOUSEEVENTF_LEFTUP):
                    log.warning("后台连线抬起失败: game=%s", lease.game_hwnd)
                    return False
                pressed = False
                return True
            finally:
                if pressed:
                    self._send_mouse_input(MOUSEEVENTF_LEFTUP)

    def mouse_click_blank(self, coordinate=(1, 1), times=1, move_back=False) -> bool:
        msg = "点击（1，1）空白位置"
        log.debug(msg, stacklevel=2)
        x = coordinate[0] + 5
        y = coordinate[1] + 5
        # _randomize_coords is applied inside mouse_click for WindowMoveInput
        return self.mouse_click(x, y, times=times)

    def _window_move_to(
        self, x_or_pos: int | tuple[int, int], y: int = -32000, duration: float = 0
    ) -> bool:
        if duration <= 0:
            self._set_window_pos(x_or_pos, y)
            return True
        else:
            if isinstance(x_or_pos, tuple):
                target_x, target_y = x_or_pos
            else:
                target_x = x_or_pos
                target_y = y
        current_x, current_y = screen.handle.mouse_pos_to_client_mouse(
            *self.get_mouse_position()
        )
        path = generate_bezier_path((current_x, current_y), (target_x, target_y))
        step_time = duration / max(1, len(path))
        for px, py in path:
            self._set_window_pos(px, py)
            if not self._mouse_move_heartbeat():
                log.warning("后台拖拽窗口移动心跳失败，中止路径")
                return False
            sleep(humanised_delay(step_time, "gaussian"))

        self._set_window_pos(target_x, target_y)
        if not self._mouse_move_heartbeat():
            log.warning("后台拖拽窗口末端心跳失败")
            return False
        return True

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
            raise RuntimeError("后台模式不支持最小化游戏窗口")
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
            raise RuntimeError("后台模式不支持物理输入驱动")
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise RuntimeError("后台模式游戏窗口句柄无效")
        moved = win32gui.SetWindowPos(
            hwnd,
            None,
            mouse_pos[0] - x + dx,
            mouse_pos[1] - y + dy,
            0,
            0,
            win32con.SWP_NOSIZE
            | win32con.SWP_NOZORDER
            | win32con.SWP_NOACTIVATE
            | win32con.SWP_NOSENDCHANGING,
        )
        if moved is False:
            raise RuntimeError("后台模式移动游戏窗口失败")

        return original_rect[:2]

    def set_active(self):
        """后台模式不抢占前台焦点，保留接口以兼容旧调用方。"""
        return

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
        if not self._send_mouse_input(MOUSEEVENTF_LEFTDOWN):
            raise RuntimeError("后台鼠标按下失败")
        sleep(0.02 + cfg.config.mouse_down_duration)

    def mouse_up(self, x, y):
        """鼠标左键抬起
        Args:
            x (number): 相对于窗口左上角的 x 轴坐标
            y (number): 相对于窗口左上角的 y 轴坐标
        """
        if self.driver:
            self.driver.mouse_up(int(x), int(y))
            return
        if not self._send_mouse_input(MOUSEEVENTF_LEFTUP):
            raise RuntimeError("后台鼠标抬起失败")
        sleep(0.02)

    def mouse_click(self, x, y, times=1, move_back=False) -> bool:
        rx, ry = self._randomize_coords(x, y)
        msg = f"点击位置:({x},{y}) -> 随机偏移后:({rx},{ry})"
        log.debug(msg, stacklevel=2)
        with self._mouse_lease(rx, ry) as lease:
            if lease is None:
                return False
            pressed = False
            try:
                for index in range(times):
                    if index:
                        rx, ry = self._randomize_coords(x, y)
                        self._set_window_pos(rx, ry)
                    # SendInput uses the unchanged physical cursor position.
                    # A zero-distance move refreshes Unity's current hit-test
                    # target after the game window is aligned beneath it.
                    if not self._mouse_move_heartbeat():
                        log.warning("后台点击鼠标位置心跳失败: game=%s", lease.game_hwnd)
                        return False
                    if not self._send_mouse_input(MOUSEEVENTF_LEFTDOWN):
                        log.warning("后台点击按下失败: game=%s", lease.game_hwnd)
                        return False
                    pressed = True
                    sleep(humanised_delay(0.05, "gaussian"))
                    if not self._send_mouse_input(MOUSEEVENTF_LEFTUP):
                        log.warning("后台点击抬起失败: game=%s", lease.game_hwnd)
                        return False
                    pressed = False
                    if times > 1 and index < times - 1:
                        sleep(humanised_delay(0.1, "gaussian"))
                self.wait_pause()
                # Give Unity time to process input events before restoring foreground
                sleep(self.INPUT_SETTLE_MS / 1000.0)
                return True
            finally:
                if pressed:
                    self._send_mouse_input(MOUSEEVENTF_LEFTUP)


BackgroundWindowInput = WindowMoveInput
