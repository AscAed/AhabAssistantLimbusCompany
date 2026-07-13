from abc import ABC, abstractmethod

class InputDriver(ABC):
    """Interface for driver-level or hardware simulation inputs."""

    @abstractmethod
    def mouse_move(self, x: int, y: int) -> None:
        """Move cursor to absolute coordinates x, y."""
        pass

    @abstractmethod
    def mouse_down(self, x: int, y: int, button: str = "left") -> None:
        """Press mouse button down at x, y."""
        pass

    @abstractmethod
    def mouse_up(self, x: int, y: int, button: str = "left") -> None:
        """Release mouse button at x, y."""
        pass

    @abstractmethod
    def key_down(self, key: str) -> None:
        """Press key down."""
        pass

    @abstractmethod
    def key_up(self, key: str) -> None:
        """Release key."""
        pass
