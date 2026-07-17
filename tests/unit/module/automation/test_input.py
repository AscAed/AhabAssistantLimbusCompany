import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from module.automation.input_handlers.bezier import generate_bezier_path
from module.automation.input_handlers.delay import humanised_delay
from module.automation.input_handlers.driver_interface import InputDriver
from module.automation.input_handlers.input import Input, BackgroundInput, WindowMoveInput

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

    with patch.object(bg_input, "get_mouse_position", return_value=(0, 0)):
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

    with patch.object(bg_input, "get_mouse_position", return_value=(0, 0)):
        bg_input.mouse_click(target_x, target_y, times=1, move_back=False)

    assert len(driver.moves) > 0
    assert len(driver.downs) == 1
    # Coordinates are randomized — check within expected range
    actual_x = driver.downs[0][0]
    actual_y = driver.downs[0][1]
    assert target_x - radius <= actual_x <= target_x + radius
    assert target_y - radius <= actual_y <= target_y + radius

# 7. Test WindowMoveInput.mouse_click uses randomized coords
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_input_randomized_click(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_cfg.config.mouse_down_duration = 0
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    driver = MockInputDriver()
    wm_input = WindowMoveInput(driver=driver)
    wm_input.set_driver(driver)

    target_x, target_y = 300, 400
    radius = 4

    with patch.object(wm_input, "get_mouse_position", return_value=(960, 540)), \
         patch.object(wm_input, "_set_window_pos", return_value=(0, 0)), \
         patch.object(wm_input, "set_active"), \
         patch("module.automation.input_handlers.input.screen.handle.set_window_pos"):
        wm_input.mouse_click(target_x, target_y, times=1)

    assert len(driver.downs) == 1
    actual_x = driver.downs[0][0]
    actual_y = driver.downs[0][1]
    assert target_x - radius <= actual_x <= target_x + radius
    assert target_y - radius <= actual_y <= target_y + radius
