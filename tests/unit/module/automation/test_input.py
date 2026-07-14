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

@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_background_input_bezier_and_driver(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = True
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    driver = MockInputDriver()
    bg_input = BackgroundInput(driver=driver)
    bg_input.set_driver(driver)
    bg_input.last_x = 10
    bg_input.last_y = 10

    with patch.object(bg_input, "get_mouse_position", return_value=(0, 0)):
        bg_input.mouse_click(50, 60, times=1, move_back=False)

    # Moves should capture path from (10, 10) to (50, 60)
    assert len(driver.moves) > 0
    assert driver.moves[-1] == (50, 60)
    assert len(driver.downs) == 1
    assert driver.ups[0][0] == 50
    assert driver.ups[0][1] == 60
