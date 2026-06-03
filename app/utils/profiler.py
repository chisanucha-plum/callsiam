"""Performance profiling utilities."""

import logging
import time
from functools import wraps
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class LatencyTracker:
    """Track latency metrics for different operations."""

    def __init__(self) -> None:
        """Initialize latency tracker."""
        self._metrics: Dict[str, List[float]] = {}

    def record(self, operation: str, latency_ms: float) -> None:
        """Record latency for an operation.

        Args:
            operation: Name of the operation.
            latency_ms: Latency in milliseconds.
        """
        if operation not in self._metrics:
            self._metrics[operation] = []
        self._metrics[operation].append(latency_ms)

    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation.

        Args:
            operation: Name of the operation.

        Returns:
            Dictionary with min, max, avg, and count.
        """
        if operation not in self._metrics or not self._metrics[operation]:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        latencies = self._metrics[operation]
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "count": len(latencies),
        }

    def print_summary(self) -> None:
        """Print summary of all tracked operations."""
        print("\n" + "=" * 60)
        print("Performance Summary")
        print("=" * 60)

        for operation in sorted(self._metrics.keys()):
            stats = self.get_stats(operation)
            print(f"\n{operation}:")
            print(f"  Count: {stats['count']}")
            print(f"  Min:   {stats['min']:.2f}ms")
            print(f"  Max:   {stats['max']:.2f}ms")
            print(f"  Avg:   {stats['avg']:.2f}ms")

        print("=" * 60 + "\n")

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()


# Global tracker instance
_tracker = LatencyTracker()


def get_tracker() -> LatencyTracker:
    """Get the global latency tracker.

    Returns:
        Global LatencyTracker instance.
    """
    return _tracker


def profile_latency(operation_name: str = None) -> Callable:
    """Decorator to measure and log function latency.

    Args:
        operation_name: Optional custom name for the operation.

    Returns:
        Decorated function.

    Example:
        @profile_latency("STT")
        def transcribe(self, audio):
            # ... implementation
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                _tracker.record(op_name, elapsed_ms)
                logger.debug(f"{op_name} took {elapsed_ms:.2f}ms")

        return wrapper

    return decorator


class Timer:
    """Context manager for timing code blocks.

    Example:
        with Timer("Processing audio"):
            process_audio()
    """

    def __init__(self, operation: str, log_level: int = logging.INFO) -> None:
        """Initialize timer.

        Args:
            operation: Name of the operation being timed.
            log_level: Logging level for the result.
        """
        self.operation = operation
        self.log_level = log_level
        self.start_time = None
        self.elapsed_ms = None

    def __enter__(self) -> "Timer":
        """Start the timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the timer and log the result."""
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        _tracker.record(self.operation, self.elapsed_ms)
        logger.log(
            self.log_level,
            f"{self.operation} took {self.elapsed_ms:.2f}ms"
        )
