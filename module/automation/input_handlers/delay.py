import random
import numpy as np

def humanised_delay(
    base_duration: float,
    distribution: str = "gaussian",
    std_dev: float | None = None
) -> float:
    """Generate a humanised delay using either Gaussian or Poisson distribution.

    Args:
        base_duration: The target/mean duration in seconds.
        distribution: Either 'gaussian' or 'poisson'.
        std_dev: Standard deviation for Gaussian (default: 30% of base_duration).

    Returns:
        A float representing the delay in seconds, with a minimum of 0.001s.
    """
    if base_duration <= 0:
        return 0.001

    if distribution.lower() == "poisson":
        # Convert base_duration to milliseconds to use as lambda for Poisson
        lam = max(1.0, base_duration * 1000.0)
        ms_delay = np.random.poisson(lam)
        delay = ms_delay / 1000.0
    else:
        # Default to gaussian
        if std_dev is None:
            std_dev = base_duration * 0.3
        delay = random.gauss(base_duration, std_dev)

    return max(0.001, delay)
