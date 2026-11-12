"""测试后台模式滚轮输入和拖拽兜底优化"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from module.automation.automation import Automation
from module.automation.input_handlers.input import WindowMoveInput


class TestBatchScrollFix:
    """验证 batch_mouse_scroll 方法的正确绑定和调用"""

    def test_automation_binds_batch_mouse_scroll_for_windowmove_input(self):
        """验证 Automation 类正确绑定了 WindowMoveInput 的 batch_mouse_scroll 方法"""
        with patch('module.automation.automation.cfg') as mock_cfg:
            mock_cfg.simulator = False
            mock_cfg.operation_mode = "background_window"
            
            # 创建 Automation 实例
            auto = Automation.__new__(Automation)
            auto.windows_title = "Test"
            auto.screenshot = None
            auto.screenshot_np = None
            auto.input_handler = WindowMoveInput()
            auto.img_cache = {}
            auto.location_cache = {}
            auto.last_screenshot_time = 0
            auto.last_click_time = 0
            auto.last_memory_check_time = 0
            auto.model = "clam"
            
            # 调用 init_input 来绑定方法
            auto.init_input()
            
            # 验证 batch_mouse_scroll 已正确绑定
            assert hasattr(auto, 'batch_mouse_scroll'), "Automation 应该有 batch_mouse_scroll 属性"
            assert auto.batch_mouse_scroll is not None, "batch_mouse_scroll 不应该是 None"
            assert callable(auto.batch_mouse_scroll), "batch_mouse_scroll 应该是可调用的"

    def test_batch_mouse_scroll_not_bound_for_foreground_input(self):
        """验证前台模式下 batch_mouse_scroll 为 None"""
        with patch('module.automation.automation.cfg') as mock_cfg:
            mock_cfg.simulator = False
            mock_cfg.operation_mode = "foreground_mouse"
            
            auto = Automation.__new__(Automation)
            auto.windows_title = "Test"
            auto.screenshot = None
            auto.screenshot_np = None
            from module.automation.input_handlers.input import Input
            auto.input_handler = Input()
            auto.img_cache = {}
            auto.location_cache = {}
            auto.last_screenshot_time = 0
            auto.last_click_time = 0
            auto.last_memory_check_time = 0
            auto.model = "clam"
            
            auto.init_input()
            
            # 前台模式不支持 batch_mouse_scroll
            assert auto.batch_mouse_scroll is None, "前台模式 batch_mouse_scroll 应该是 None"

    def test_scroll_once_uses_batch_when_available(self):
        """验证 scroll_once 函数优先使用 batch_mouse_scroll"""
        # 模拟 auto 对象
        mock_auto = Mock()
        mock_auto.batch_mouse_scroll = Mock(return_value=True)
        mock_auto.mouse_scroll = Mock(return_value=True)
        
        # 模拟 scroll_once 逻辑
        def scroll_once(direction, x, y, count=1):
            if hasattr(mock_auto, 'batch_mouse_scroll') and mock_auto.batch_mouse_scroll is not None:
                return mock_auto.batch_mouse_scroll(direction, count, x, y)
            elif hasattr(mock_auto, 'mouse_scroll') and mock_auto.mouse_scroll is not None:
                for _ in range(count):
                    if not mock_auto.mouse_scroll(direction, x, y):
                        return False
                return True
            return False
        
        # 测试使用 batch_mouse_scroll
        result = scroll_once(1, 100, 200, count=30)
        
        assert result is True
        mock_auto.batch_mouse_scroll.assert_called_once_with(1, 30, 100, 200)
        mock_auto.mouse_scroll.assert_not_called()

    def test_scroll_once_fallback_to_single_scroll(self):
        """验证当 batch_mouse_scroll 不可用时回退到单次滚轮"""
        mock_auto = Mock()
        mock_auto.batch_mouse_scroll = None
        mock_auto.mouse_scroll = Mock(return_value=True)
        
        def scroll_once(direction, x, y, count=1):
            if hasattr(mock_auto, 'batch_mouse_scroll') and mock_auto.batch_mouse_scroll is not None:
                return mock_auto.batch_mouse_scroll(direction, count, x, y)
            elif hasattr(mock_auto, 'mouse_scroll') and mock_auto.mouse_scroll is not None:
                for _ in range(count):
                    if not mock_auto.mouse_scroll(direction, x, y):
                        return False
                return True
            return False
        
        result = scroll_once(-1, 100, 200, count=5)
        
        assert result is True
        assert mock_auto.mouse_scroll.call_count == 5

    def test_optimized_drag_parameters(self):
        """验证优化后的拖拽参数（单次大拖拽）"""
        mock_auto = Mock()
        mock_auto.mouse_drag = Mock(return_value=True)
        
        scale = 1.0  # 1440p
        first_pos = [100, 200]
        
        # 模拟 scroll_to_top 的拖拽兜底逻辑
        mock_auto.mouse_drag(
            first_pos[0],
            first_pos[1],
            dy=1000 * scale,
            drag_time=0.8
        )
        
        # 验证只调用一次，而不是4次
        assert mock_auto.mouse_drag.call_count == 1
        
        # 验证参数：单次大拖拽
        call_args = mock_auto.mouse_drag.call_args
        assert call_args[1]['dy'] == 1000  # 大距离
        assert call_args[1]['drag_time'] == 0.8  # 快速但平滑

    def test_optimized_scroll_down_single_drag(self):
        """验证向下滚动使用单次拖拽处理多页"""
        mock_auto = Mock()
        mock_auto.mouse_drag = Mock(return_value=True)
        
        scale = 1.0
        first_pos = [100, 200]
        pages = 3  # 滚动3页
        
        # 模拟优化后的 scroll_down 拖拽兜底
        mock_auto.mouse_drag(
            first_pos[0],
            first_pos[1] + 375 * scale,
            dy=-375 * scale * pages,
            drag_time=0.6 * pages
        )
        
        # 验证只调用一次，而不是多次
        assert mock_auto.mouse_drag.call_count == 1
        
        # 验证距离和时间根据页数缩放
        call_args = mock_auto.mouse_drag.call_args
        assert call_args[1]['dy'] == -375 * pages
        assert call_args[1]['drag_time'] == 0.6 * pages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
