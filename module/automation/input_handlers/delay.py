
def humanised_delay(
    base_duration: float,
    distribution: str = "gaussian",
    std_dev: float | None = None
) -> float:
    """Return a deterministic bounded delay for input operations.

    Args:
        base_duration: The target/mean duration in seconds.
        distribution: Kept for API compatibility.
        std_dev: Kept for API compatibility.

    Returns:
        A float representing the delay in seconds, with a minimum of 0.001s.
    """
    if base_duration <= 0:
        return 0.001
    return max(0.001, base_duration)
