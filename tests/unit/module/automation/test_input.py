from unittest.mock import patch

import pytest

from module.automation.input_handlers.bezier import generate_bezier_path
from module.automation.input_handlers.delay import humanised_delay
from module.automation.input_handlers.driver_interface import InputDriver
from module.automation.input_handlers.input import BackgroundInput, Input, WindowMoveInput, human_delay


# 1. Test Bezier Path Generator
def test_generate_bezier_path():
    start = (10, 20)
    end = (100, 200)
    
    # Verify that a path is generated
    path = generate_bezier_path(start, end, steps=10)
    assert len(path) == 11
    assert path[0] == start
    assert path[-1] == end

    # Test short distance paths
    short_path = generate_bezier_path((1, 1), (2, 2))
    assert len(short_path) >= 2
    assert short_path[0] == (1, 1)
    assert short_path[-1] == (2, 2)


def test_generate_bezier_path_is_deterministic():
    start = (10, 20)
    end = (100, 200)

    assert generate_bezier_path(start, end, steps=10) == generate_bezier_path(start, end, steps=10)

# 2. Test Humanised Delays
def test_humanised_delay():
    # Gaussian
    for _ in range(50):
        delay = humanised_delay(0.05, "gaussian")
        assert delay >= 0.001

    # Poisson
    for _ in range(50):
        delay = humanised_delay(0.05, "poisson")
        assert delay >= 0.001


def test_human_delay_is_deterministic():
    assert human_delay(0.1, 0.03) == 0.1
    assert human_delay(0.001, 0.03) == 0.01


def test_humanised_delay_is_deterministic():
    assert humanised_delay(0.05, "gaussian") == 0.05
    assert humanised_delay(0.05, "poisson") == 0.05

# 3. Test Driver-level Interface and Delegation
class MockInputDriver(InputDriver):
    def __init__(self):
        self.moves = []
        self.downs = []
        self.ups = []
        self.key_downs = []
        self.key_ups = []

    def mouse_move(self, x: int, y: int) -> None:
        self.moves.append((x, y))

    def mouse_down(self, x: int, y: int, button: str = "left") -> None:
        self.downs.append((x, y, button))

    def mouse_up(self, x: int, y: int, button: str = "left") -> None:
        self.ups.append((x, y, button))

    def key_down(self, key: str) -> None:
        self.key_downs.append(key)

    def key_up(self, key: str) -> None:
        self.key_ups.append(key)

@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_driver_delegation(mock_cfg, mock_screen):
    # Mock configuration and screen handle
    mock_cfg.config.use_post_message = True
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False
    
    driver = MockInputDriver()
    
    # Retrieve singletons
    input_handler = Input(driver=driver)
    input_handler.set_driver(driver)
    
    # Trigger mouse down/up via mouse_click
    # We patch get_mouse_position to return start location to avoid pywintypes/win32 api dependency issues
    with patch.object(input_handler, "get_mouse_position", return_value=(0, 0)):
        input_handler.mouse_click(100, 100, times=1, move_back=False)
        
    # Verify driver received move and click calls
    assert len(driver.moves) > 0
    assert len(driver.downs) == 1
    assert len(driver.ups) == 1
    # Check absolute coords (pos_offset should add window rect start)
    assert driver.downs[0][0] == 100
    assert driver.downs[0][1] == 100

# 4. Test _randomize_coords applies a bounded offset
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_randomize_coords_bounded_offset(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    handler = BackgroundInput()
    radius = 4
    for _ in range(100):
        rx, ry = handler._randomize_coords(100, 200, radius=radius)
        assert 100 - radius <= rx <= 100 + radius, f"rx={rx} out of bounds"
        assert 200 - radius <= ry <= 200 + radius, f"ry={ry} out of bounds"


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_randomize_coords_is_deterministic(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    handler = BackgroundInput()
    assert handler._randomize_coords(100, 200) == (100, 200)
    assert handler._randomize_coords(100, 200, radius=10) == (100, 200)

# 5. Test BackgroundInput.mouse_click uses randomized coords and move_back defaults to False
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_input_randomized_click(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    driver = MockInputDriver()
    bg_input = BackgroundInput(driver=driver)
    bg_input.set_driver(driver)
    bg_input.last_x = 10
    bg_input.last_y = 10

    target_x, target_y = 50, 60
    radius = 4

    with patch.object(bg_input, "get_mouse_position", return_value=(0, 0)), patch.object(
        bg_input, "set_active"
    ):
        # Default move_back=False; if it were True, get_mouse_position would be called
        bg_input.mouse_click(target_x, target_y, times=1)

    assert len(driver.downs) == 1
    assert len(driver.ups) == 1
    # Coordinates must be within the randomization radius
    actual_x = driver.downs[0][0]
    actual_y = driver.downs[0][1]
    assert target_x - radius <= actual_x <= target_x + radius, f"click x={actual_x} not within radius"
    assert target_y - radius <= actual_y <= target_y + radius, f"click y={actual_y} not within radius"

# 6. Test BackgroundInput.mouse_click legacy test updated for randomized coords
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_input_bezier_and_driver(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    driver = MockInputDriver()
    bg_input = BackgroundInput(driver=driver)
    bg_input.set_driver(driver)
    bg_input.last_x = 10
    bg_input.last_y = 10

    target_x, target_y = 50, 60
    radius = 4

    with patch.object(bg_input, "get_mouse_position", return_value=(0, 0)), patch.object(
        bg_input, "set_active"
    ):
        bg_input.mouse_click(target_x, target_y, times=1, move_back=False)

    assert len(driver.moves) > 0
    assert len(driver.downs) == 1
    # Coordinates are randomized — check within expected range
    actual_x = driver.downs[0][0]
    actual_y = driver.downs[0][1]
    assert target_x - radius <= actual_x <= target_x + radius
    assert target_y - radius <= actual_y <= target_y + radius


@patch("module.automation.input_handlers.input.generate_bezier_path", side_effect=lambda start, end: [start, end])
@patch("module.automation.input_handlers.input.win32gui.SendMessage")
@patch("module.automation.input_handlers.input.win32api.SetCursorPos")
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_drag_link_syncs_cursor_before_press(
    mock_cfg,
    mock_screen,
    mock_set_cursor_pos,
    mock_send_message,
    _mock_path,
):
    import win32con

    mock_cfg.config.use_post_message = False
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isActive = True
    mock_screen.handle.rect.return_value = (10, 20, 1920, 1080)

    handler = BackgroundInput()
    handler.set_driver(None)
    handler.use_post_message = False
    events = []
    mock_set_cursor_pos.side_effect = lambda pos: events.append(("cursor", pos))

    with patch.object(handler, "set_active"), \
         patch.object(handler, "_post_bezier_move"), \
         patch.object(handler, "mouse_down", side_effect=lambda x, y: events.append(("down", x, y))), \
         patch.object(handler, "mouse_up", side_effect=lambda x, y: events.append(("up", x, y))):
        handler.mouse_drag_link([(100, 200), (300, 400)], drag_time=0)

    assert mock_set_cursor_pos.call_args_list[0].args[0] == (110, 220)
    assert mock_set_cursor_pos.call_args_list[-1].args[0] == (310, 420)
    assert events[0] == ("cursor", (110, 220))
    assert events[1] == ("down", 100, 200)
    assert events[-2] == ("cursor", (310, 420))
    assert events[-1] == ("up", 300, 400)
    move_messages = [
        call for call in mock_send_message.call_args_list if call.args[1] == win32con.WM_MOUSEMOVE
    ]
    assert move_messages
    assert all(call.args[2] == win32con.MK_LBUTTON for call in move_messages)


@patch("module.automation.input_handlers.input.generate_bezier_path", side_effect=lambda start, end: [start, end])
@patch("module.automation.input_handlers.input.win32api.SetCursorPos")
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_drag_link_resolves_release_after_fixed_points(
    mock_cfg,
    mock_screen,
    mock_set_cursor_pos,
    _mock_path,
):
    mock_cfg.config.use_post_message = False
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isActive = True
    mock_screen.handle.rect.return_value = (10, 20, 1920, 1080)

    handler = BackgroundInput()
    events = []
    mock_set_cursor_pos.side_effect = lambda pos: events.append(("cursor", pos))

    def resolve_release():
        events.append(("resolve",))
        return 500, 600

    with patch.object(handler, "set_active"), \
         patch.object(handler, "_post_bezier_move"), \
         patch.object(handler, "mouse_down", side_effect=lambda x, y: events.append(("down", x, y))), \
         patch.object(handler, "mouse_up", side_effect=lambda x, y: events.append(("up", x, y))):
        handler.mouse_drag_link(
            [(100, 200), (300, 400)],
            drag_time=0,
            resolve_last_position=resolve_release,
        )

    assert events[1] == ("down", 100, 200)
    assert events.index(("resolve",)) > events.index(("down", 100, 200))
    assert events[-2] == ("cursor", (510, 620))
    assert events[-1] == ("up", 500, 600)


@patch("module.automation.input_handlers.input.generate_bezier_path", side_effect=lambda start, end: [start, end])
@patch("module.automation.input_handlers.input.win32api.SetCursorPos")
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_drag_link_does_not_move_inactive_cursor(
    mock_cfg,
    mock_screen,
    mock_set_cursor_pos,
    _mock_path,
):
    mock_cfg.config.use_post_message = False
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isActive = False

    handler = BackgroundInput()
    handler.set_driver(None)
    handler.use_post_message = False

    with patch.object(handler, "set_active"), \
         patch.object(handler, "_post_bezier_move"), \
         patch.object(handler, "mouse_down"), \
         patch.object(handler, "mouse_up"), \
         patch("module.automation.input_handlers.input.win32gui.SendMessage"):
        handler.mouse_drag_link([(100, 200), (300, 400)], drag_time=0)

    mock_set_cursor_pos.assert_not_called()


@patch("module.automation.input_handlers.input.generate_bezier_path", side_effect=lambda start, end: [start, end])
@patch("module.automation.input_handlers.input.win32gui.SendMessage", side_effect=RuntimeError("move failed"))
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_drag_link_releases_when_move_fails(
    mock_cfg,
    mock_screen,
    _mock_send_message,
    _mock_path,
):
    mock_cfg.config.use_post_message = False
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isActive = False

    handler = BackgroundInput()
    handler.set_driver(None)
    handler.use_post_message = False

    with patch.object(handler, "set_active"), \
         patch.object(handler, "_post_bezier_move"), \
         patch.object(handler, "mouse_down"), \
         patch.object(handler, "mouse_up") as mock_mouse_up:
        with pytest.raises(RuntimeError, match="move failed"):
            handler.mouse_drag_link([(100, 200), (300, 400)], drag_time=0)

    mock_mouse_up.assert_called_once_with(100, 200)


# 7. WindowMoveInput rejects physical input drivers
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_input_rejects_driver(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    handler = WindowMoveInput(driver=object())
    handler.is_pause = False
    handler.restore_time = None
    with patch.object(handler, "_set_window_pos", side_effect=RuntimeError("后台模式不支持物理输入驱动")), \
        patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "get_mouse_position", return_value=(960, 540)):
        with pytest.raises(RuntimeError, match="物理输入驱动"):
            handler.mouse_click(300, 400)


# 8. Test BackgroundInput.mouse_scroll uses descendant hwnd when found window is a child of game hwnd
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_scroll_uses_descendant_hwnd(mock_cfg, mock_screen):
    """When WindowFromPoint returns a direct child of the game hwnd, the scroll message should
    be posted to that child (not the parent), so Unity's render sub-window receives the event.
    Also verifies the wheel lands on the child hwnd that Unity is expected to read from."""
    import win32con

    game_hwnd = 1000
    child_hwnd = 1001

    mock_cfg.config.use_post_message = True
    mock_cfg.set_win_size = 1080
    mock_screen.handle.hwnd = game_hwnd
    mock_screen.handle.isMinimized = False

    bg_input = BackgroundInput()

    with patch("win32gui.ClientToScreen", return_value=(960, 540)), \
         patch("win32api.MAKELONG", return_value=0), \
         patch.object(bg_input, "_mouse_move_to"), \
         patch("win32gui.WindowFromPoint", return_value=child_hwnd), \
         patch("win32gui.GetParent", return_value=game_hwnd), \
        patch("win32api.PostMessage") as mock_post:
        result = bg_input.mouse_scroll(-3)

    assert result is True
    calls = mock_post.call_args_list
    # Expect at least: WM_MOUSEMOVE and WM_MOUSEWHEEL
    messages = [c[0][1] for c in calls]
    assert win32con.WM_MOUSEWHEEL in messages, "WM_MOUSEWHEEL not posted"
    # The final WM_MOUSEWHEEL must target the child hwnd
    wheel_call = next(c for c in reversed(calls) if c[0][1] == win32con.WM_MOUSEWHEEL)
    assert wheel_call[0][0] == child_hwnd, f"Expected child hwnd {child_hwnd}, got {wheel_call[0][0]}"
    # wparam for scroll-down (-3 * 120 = -360) must be negative (no 0xFFFFFFFF mask)
    wheel_wparam = wheel_call[0][2]
    assert wheel_wparam < 0, f"wparam should be negative for scroll-down, got {wheel_wparam}"


# 9. Test BackgroundInput.mouse_scroll resolves child hwnd via EnumChildWindows when found window is foreign
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_scroll_resolves_child_for_foreign_hwnd(mock_cfg, mock_screen):
    """When WindowFromPoint returns a window that is NOT a descendant of the game hwnd (e.g. the
    script console is in front), the scroll message must resolve the game's child window via EnumChildWindows."""
    import win32con

    game_hwnd = 1000
    foreign_hwnd = 9999  # belongs to a completely different process
    resolved_child = 2002  # game's child window resolved programmatically

    mock_cfg.config.use_post_message = True
    mock_cfg.set_win_size = 1080
    mock_screen.handle.hwnd = game_hwnd
    mock_screen.handle.isMinimized = False

    bg_input = BackgroundInput()

    def fake_get_parent(hwnd):
        return 0  # foreign window has no parent

    def fake_enum_child(hwnd, callback, param):
        callback(resolved_child, param)

    with patch("win32gui.ClientToScreen", return_value=(960, 540)), \
         patch("win32api.MAKELONG", return_value=0), \
         patch.object(bg_input, "_mouse_move_to"), \
         patch("win32gui.WindowFromPoint", return_value=foreign_hwnd), \
         patch("win32gui.GetParent", side_effect=fake_get_parent), \
         patch("win32gui.EnumChildWindows", side_effect=fake_enum_child), \
        patch("win32api.PostMessage") as mock_post:
        result = bg_input.mouse_scroll(-3)

    assert result is True
    calls = mock_post.call_args_list
    messages = [c[0][1] for c in calls]
    assert win32con.WM_SETFOCUS in messages, "WM_SETFOCUS not posted"
    assert win32con.WM_MOUSEWHEEL in messages, "WM_MOUSEWHEEL not posted"
    # WM_MOUSEWHEEL must target the resolved child window (2002)
    wheel_call = next(c for c in reversed(calls) if c[0][1] == win32con.WM_MOUSEWHEEL)
    assert wheel_call[0][0] == resolved_child, f"Expected resolved child handle {resolved_child}, got {wheel_call[0][0]}"


# 10. Test BackgroundInput.mouse_scroll falls back to root game hwnd if EnumChildWindows finds no children
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_scroll_falls_back_to_root_if_no_children(mock_cfg, mock_screen):
    """When WindowFromPoint returns a foreign window and EnumChildWindows finds no children, it should fall back to root game hwnd."""
    import win32con

    game_hwnd = 1000
    foreign_hwnd = 9999

    mock_cfg.config.use_post_message = True
    mock_cfg.set_win_size = 1080
    mock_screen.handle.hwnd = game_hwnd
    mock_screen.handle.isMinimized = False

    bg_input = BackgroundInput()

    with patch("win32gui.ClientToScreen", return_value=(960, 540)), \
         patch("win32api.MAKELONG", return_value=0), \
         patch.object(bg_input, "_mouse_move_to"), \
         patch("win32gui.WindowFromPoint", return_value=foreign_hwnd), \
         patch("win32gui.GetParent", return_value=0), \
         patch("win32gui.EnumChildWindows"), \
         patch("win32gui.SetForegroundWindow"), \
         patch("win32api.PostMessage") as mock_post:
        result = bg_input.mouse_scroll(-3)

    assert result is True
    calls = mock_post.call_args_list
    wheel_call = next(c for c in reversed(calls) if c[0][1] == win32con.WM_MOUSEWHEEL)
    assert wheel_call[0][0] == game_hwnd, f"Expected root game hwnd {game_hwnd}, got {wheel_call[0][0]}"


# 11. Test BackgroundInput.mouse_scroll with specific coordinates
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_scroll_with_coordinates(mock_cfg, mock_screen):
    """When coordinates are specified to mouse_scroll, ClientToScreen must be called with those coordinates."""
    game_hwnd = 1000
    mock_cfg.config.use_post_message = True
    mock_cfg.set_win_size = 1080
    mock_screen.handle.hwnd = game_hwnd
    mock_screen.handle.isMinimized = False

    bg_input = BackgroundInput()

    with patch("win32gui.ClientToScreen", return_value=(200, 300)) as mock_client_to_screen, \
         patch("win32api.MAKELONG", return_value=0), \
         patch.object(bg_input, "_mouse_move_to"), \
         patch("win32gui.WindowFromPoint", return_value=game_hwnd), \
         patch("win32gui.SetForegroundWindow"), \
         patch("win32api.PostMessage"):
        result = bg_input.mouse_scroll(-3, x=192, y=864)

    assert result is True
    mock_client_to_screen.assert_called_once_with(game_hwnd, (192, 864))



