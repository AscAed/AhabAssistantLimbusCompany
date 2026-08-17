import sys
from unittest.mock import MagicMock

# Mock windows specific modules required for linux testing
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['pywintypes'] = MagicMock()
sys.modules['pywintypes'].error = type('error', (Exception,), {})
sys.modules['win32ui'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['win32crypt'] = MagicMock()
sys.modules['rapidocr'] = MagicMock()
sys.modules['rapidocr_onnxruntime'] = MagicMock()
sys.modules['rapidocr.utils'] = MagicMock()
sys.modules['rapidocr.utils.output'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
sys.modules['pynput'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['vlc'] = MagicMock()
