from enum import Enum
import time
from time import sleep

from PySide6.QtCore import QObject

from app import mediator
from module.automation import auto
from module.automation.automation import GameState, PageStateDispatcher
from module.config import cfg
from module.logger import log
from module.my_error.my_error import userStopError

class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Task:
    def __init__(self, name: str, allowed_start_states: list[str] = None):
        self.name = name
        self.status = TaskStatus.PENDING
        self.allowed_start_states = allowed_start_states or [GameState.MAIN_MENU]
        self.error = None

    def run(self, engine) -> bool:
        raise NotImplementedError


class MakeEnkephalinTask(Task):
    def __init__(self):
        super().__init__("合成脑啡肽", [GameState.MAIN_MENU])

    def run(self, engine) -> bool:
        from tasks.base.make_enkephalin_module import make_enkephalin_module
        make_enkephalin_module()
        return True


class DailyLuxcavationTask(Task):
    def __init__(self):
        super().__init__("每日副本 (经验/纽扣)", [
            GameState.MAIN_MENU, GameState.BATTLE, GameState.BATTLE_FORMATION
        ])

    def run(self, engine) -> bool:
        from tasks.base.script_task_scheme import Daily_task_wrapper
        # Let daily task wrapper execute
        wrapper = Daily_task_wrapper(get_reward=engine.get_reward_context)
        wrapper()
        return True


class GetRewardTask(Task):
    def __init__(self):
        super().__init__("领取奖励 (邮箱/通行证)", [GameState.MAIN_MENU])

    def run(self, engine) -> bool:
        from tasks.base.script_task_scheme import to_get_reward
        to_get_reward()
        return True


class BuyEnkephalinTask(Task):
    def __init__(self):
        super().__init__("脑啡肽购买 (狂气转换)", [GameState.MAIN_MENU])

    def run(self, engine) -> bool:
        from tasks.base.script_task_scheme import Buy_enkephalin
        Buy_enkephalin()
        return True


class MirrorDungeonTask(Task):
    def __init__(self):
        super().__init__("镜牢 (镜像迷宫)", [
            GameState.MAIN_MENU, GameState.MIRROR_ENTRANCE, GameState.ROAD_MAP,
            GameState.SHOP, GameState.EVENT, GameState.BATTLE_FORMATION,
            GameState.BATTLE, GameState.EGO_GIFT_SELECT, GameState.CLAIM_REWARD,
            GameState.MIRROR_TEAM_SELECT, GameState.THEME_PACK
        ])

    def run(self, engine) -> bool:
        from tasks.base.script_task_scheme import Mirror_task
        Mirror_task()
        return True


class TaskEngine:
    def __init__(self, thread=None):
        self.thread = thread
        self.tasks: list[Task] = []
        self.dispatcher = PageStateDispatcher(auto)
        self.get_reward_context = None
        self._original_take_screenshot = None

    def add_task(self, task: Task):
        self.tasks.append(task)

    def _setup_screenshot_hook(self):
        """Monkey-patch auto.take_screenshot to cooperatively raise userStopError when thread is stopped."""
        self._original_take_screenshot = auto.take_screenshot
        
        def hook_take_screenshot(*args, **kwargs):
            if self.thread and getattr(self.thread, "is_stop", False):
                raise userStopError("用户主动终止程序")
            return self._original_take_screenshot(*args, **kwargs)

        auto.take_screenshot = hook_take_screenshot

    def _restore_screenshot_hook(self):
        if self._original_take_screenshot:
            auto.take_screenshot = self._original_take_screenshot

    def run(self):
        self._setup_screenshot_hook()
        try:
            for task in self.tasks:
                if self.thread and getattr(self.thread, "is_stop", False):
                    raise userStopError("用户主动终止程序")

                log.info(f"==> 任务引擎：准备执行任务 [{task.name}]")
                task.status = TaskStatus.RUNNING

                # 1. 自动页面状态检测与自适应导航
                state = self.dispatcher.detect_state()
                log.info(f"==> 任务引擎：当前游戏页面状态为 [{state}]")

                if state not in task.allowed_start_states:
                    log.info(f"==> 任务引擎：当前状态不在允许的起始状态列表 {task.allowed_start_states} 中，将自动返回主菜单导航")
                    from tasks.base.back_init_menu import back_init_menu
                    back_init_menu(allow_restart=True)
                    state = self.dispatcher.detect_state()

                # 2. 执行任务
                try:
                    success = task.run(self)
                    if success is False:
                        task.status = TaskStatus.FAILED
                        log.error(f"==> 任务引擎：任务 [{task.name}] 执行失败")
                    else:
                        task.status = TaskStatus.SUCCESS
                        log.info(f"==> 任务引擎：任务 [{task.name}] 执行完成")
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = e
                    log.exception(f"==> 任务引擎：任务 [{task.name}] 运行抛出异常")
                    # 尝试本任务失败后的局部恢复
                    log.warning("==> 任务引擎：尝试进行故障恢复并返回主页面...")
                    try:
                        from tasks.base.back_init_menu import back_init_menu
                        back_init_menu(allow_restart=False)
                    except Exception:
                        pass
                    raise e
        finally:
            self._restore_screenshot_hook()
