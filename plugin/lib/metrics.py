"""
Simple metrics collection for monitoring and observability.

This module provides:
- MetricsCollector class for tracking application metrics
- Counter, Gauge, and Histogram metric types
- API call tracking with tokens, latency, and success rates
- Thread-safe metric updates
- Prometheus export format support

Usage:
    from plugin.lib.metrics import MetricsCollector

    metrics = MetricsCollector()
    metrics.record_api_call("claude", tokens=1500, latency_ms=250.5, success=True)
    summary = metrics.get_summary()
"""

from __future__ import annotations

import statistics
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Counter:
    """
    A counter metric that only increases.

    Attributes:
        value: Current counter value
        lock: Thread lock for safe updates
    """

    value: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def increment(self, amount: int = 1) -> None:
        """
        Increment the counter.

        Args:
            amount: Amount to increment by (default: 1)
        """
        with self.lock:
            self.value += amount

    def get(self) -> int:
        """
        Get current counter value.

        Returns:
            Current value
        """
        with self.lock:
            return self.value

    def reset(self) -> None:
        """
        Reset counter to zero.
        """
        with self.lock:
            self.value = 0


@dataclass
class Gauge:
    """
    A gauge metric that can increase or decrease.

    Attributes:
        value: Current gauge value
        lock: Thread lock for safe updates
    """

    value: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set(self, value: float) -> None:
        """
        Set the gauge value.

        Args:
            value: New value
        """
        with self.lock:
            self.value = value

    def increment(self, amount: float = 1.0) -> None:
        """
        Increment the gauge.

        Args:
            amount: Amount to increment by (default: 1.0)
        """
        with self.lock:
            self.value += amount

    def decrement(self, amount: float = 1.0) -> None:
        """
        Decrement the gauge.

        Args:
            amount: Amount to decrement by (default: 1.0)
        """
        with self.lock:
            self.value -= amount

    def get(self) -> float:
        """
        Get current gauge value.

        Returns:
            Current value
        """
        with self.lock:
            return self.value

    def reset(self) -> None:
        """
        Reset gauge to zero.
        """
        with self.lock:
            self.value = 0.0


@dataclass
class Histogram:
    """
    A histogram metric for tracking distributions.

    Attributes:
        values: List of recorded values
        lock: Thread lock for safe updates
    """

    values: list[float] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def observe(self, value: float) -> None:
        """
        Record a new observation.

        Args:
            value: Value to record
        """
        with self.lock:
            self.values.append(value)

    def get_stats(self) -> dict[str, float]:
        """
        Get statistical summary of recorded values.

        Returns:
            Dictionary with min, max, mean, median, p95, p99, count

        Example:
            >>> histogram = Histogram()
            >>> histogram.observe(10.0)
            >>> histogram.observe(20.0)
            >>> stats = histogram.get_stats()
            >>> print(stats["mean"])
            15.0
        """
        with self.lock:
            if not self.values:
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "median": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                    "count": 0,
                }

            sorted_values = sorted(self.values)
            count = len(sorted_values)

            return {
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": statistics.mean(sorted_values),
                "median": statistics.median(sorted_values),
                "p95": sorted_values[int(count * 0.95)] if count > 0 else 0.0,
                "p99": sorted_values[int(count * 0.99)] if count > 0 else 0.0,
                "count": count,
            }

    def reset(self) -> None:
        """
        Clear all recorded values.
        """
        with self.lock:
            self.values.clear()


class MetricsCollector:
    """
    Thread-safe metrics collector for application monitoring.

    Tracks API calls, tokens, errors, and latency with support for
    multiple providers and Prometheus export format.

    Attributes:
        start_time: Timestamp when collector was created
        counters: Dictionary of counter metrics
        gauges: Dictionary of gauge metrics
        histograms: Dictionary of histogram metrics
        lock: Global lock for thread safety
    """

    def __init__(self) -> None:
        """
        Initialize metrics collector.
        """
        self.start_time = datetime.now(timezone.utc)
        self.lock = threading.Lock()

        # Initialize metric dictionaries
        self.counters: dict[str, Counter] = defaultdict(Counter)
        self.gauges: dict[str, Gauge] = defaultdict(Gauge)
        self.histograms: dict[str, Histogram] = defaultdict(Histogram)

        # Initialize standard metrics
        self._init_standard_metrics()

    def _init_standard_metrics(self) -> None:
        """
        Initialize standard metrics for common operations.
        """
        # API call counters
        self.counters["api_calls_total"] = Counter()
        self.counters["api_calls_success"] = Counter()
        self.counters["api_calls_error"] = Counter()

        # Token counters
        self.counters["tokens_input_total"] = Counter()
        self.counters["tokens_output_total"] = Counter()
        self.counters["tokens_total"] = Counter()

        # Error counter
        self.counters["errors_total"] = Counter()

        # Latency histogram
        self.histograms["api_latency_ms"] = Histogram()

    def record_api_call(
        self,
        provider: str,
        tokens: int,
        latency_ms: float,
        success: bool,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        """
        Record an API call with its metrics.

        Args:
            provider: API provider name (e.g., "claude", "gemini")
            tokens: Total tokens used
            latency_ms: Latency in milliseconds
            success: Whether the call succeeded
            input_tokens: Input tokens (if available)
            output_tokens: Output tokens (if available)

        Example:
            >>> metrics = MetricsCollector()
            >>> metrics.record_api_call(
            ...     provider="claude",
            ...     tokens=1500,
            ...     latency_ms=250.5,
            ...     success=True,
            ...     input_tokens=1000,
            ...     output_tokens=500,
            ... )
        """
        # Increment total calls
        self.counters["api_calls_total"].increment()
        self.counters[f"api_calls_{provider}_total"].increment()

        # Increment success/error
        if success:
            self.counters["api_calls_success"].increment()
            self.counters[f"api_calls_{provider}_success"].increment()
        else:
            self.counters["api_calls_error"].increment()
            self.counters[f"api_calls_{provider}_error"].increment()

        # Record tokens
        self.counters["tokens_total"].increment(tokens)
        self.counters[f"tokens_{provider}_total"].increment(tokens)

        if input_tokens is not None:
            self.counters["tokens_input_total"].increment(input_tokens)
            self.counters[f"tokens_{provider}_input"].increment(input_tokens)

        if output_tokens is not None:
            self.counters["tokens_output_total"].increment(output_tokens)
            self.counters[f"tokens_{provider}_output"].increment(output_tokens)

        # Record latency
        self.histograms["api_latency_ms"].observe(latency_ms)
        self.histograms[f"api_latency_{provider}_ms"].observe(latency_ms)

    def increment_counter(self, name: str, amount: int = 1) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            amount: Amount to increment by (default: 1)

        Example:
            >>> metrics.increment_counter("slides_generated", 5)
        """
        self.counters[name].increment(amount)

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Gauge name
            value: New value

        Example:
            >>> metrics.set_gauge("active_requests", 3)
        """
        self.gauges[name].set(value)

    def increment_gauge(self, name: str, amount: float = 1.0) -> None:
        """
        Increment a gauge metric.

        Args:
            name: Gauge name
            amount: Amount to increment by (default: 1.0)
        """
        self.gauges[name].increment(amount)

    def decrement_gauge(self, name: str, amount: float = 1.0) -> None:
        """
        Decrement a gauge metric.

        Args:
            name: Gauge name
            amount: Amount to decrement by (default: 1.0)
        """
        self.gauges[name].decrement(amount)

    def observe_histogram(self, name: str, value: float) -> None:
        """
        Record a histogram observation.

        Args:
            name: Histogram name
            value: Value to observe

        Example:
            >>> metrics.observe_histogram("slide_generation_time_ms", 1250.5)
        """
        self.histograms[name].observe(value)

    def record_error(self, error_type: str) -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type of error

        Example:
            >>> metrics.record_error("api_timeout")
        """
        self.counters["errors_total"].increment()
        self.counters[f"errors_{error_type}"].increment()

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary of all metrics.

        Returns:
            Dictionary with all metric values

        Example:
            >>> summary = metrics.get_summary()
            >>> print(summary["api_calls_total"])
            42
        """
        with self.lock:
            summary: dict[str, Any] = {
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                "counters": {},
                "gauges": {},
                "histograms": {},
            }

            # Add all counters
            for name, counter in self.counters.items():
                summary["counters"][name] = counter.get()

            # Add all gauges
            for name, gauge in self.gauges.items():
                summary["gauges"][name] = gauge.get()

            # Add all histograms
            for name, histogram in self.histograms.items():
                summary["histograms"][name] = histogram.get_stats()

            return summary

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string

        Example:
            >>> prometheus_output = metrics.export_prometheus()
            >>> print(prometheus_output)
            # HELP api_calls_total Total number of API calls
            # TYPE api_calls_total counter
            api_calls_total 42
        """
        lines: list[str] = []

        # Export counters
        for name, counter in self.counters.items():
            lines.append(f"# HELP {name} Counter metric")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {counter.get()}")
            lines.append("")

        # Export gauges
        for name, gauge in self.gauges.items():
            lines.append(f"# HELP {name} Gauge metric")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {gauge.get()}")
            lines.append("")

        # Export histograms (as summary in Prometheus format)
        for name, histogram in self.histograms.items():
            stats = histogram.get_stats()
            lines.append(f"# HELP {name} Histogram metric")
            lines.append(f"# TYPE {name} summary")
            lines.append(f'{name}{{quantile="0.5"}} {stats["median"]}')
            lines.append(f'{name}{{quantile="0.95"}} {stats["p95"]}')
            lines.append(f'{name}{{quantile="0.99"}} {stats["p99"]}')
            lines.append(f"{name}_sum {sum(histogram.values)}")
            lines.append(f"{name}_count {stats['count']}")
            lines.append("")

        return "\n".join(lines)

    def reset(self) -> None:
        """
        Reset all metrics to initial state.
        """
        with self.lock:
            for counter in self.counters.values():
                counter.reset()
            for gauge in self.gauges.values():
                gauge.reset()
            for histogram in self.histograms.values():
                histogram.reset()

            self.start_time = datetime.now(timezone.utc)

    def get_counter(self, name: str) -> int:
        """
        Get value of a specific counter.

        Args:
            name: Counter name

        Returns:
            Counter value
        """
        return self.counters[name].get()

    def get_gauge(self, name: str) -> float:
        """
        Get value of a specific gauge.

        Args:
            name: Gauge name

        Returns:
            Gauge value
        """
        return self.gauges[name].get()

    def get_histogram_stats(self, name: str) -> dict[str, float]:
        """
        Get statistics for a specific histogram.

        Args:
            name: Histogram name

        Returns:
            Dictionary with histogram statistics
        """
        return self.histograms[name].get_stats()


# Global metrics instance
_global_metrics: MetricsCollector | None = None
_global_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """
    Get or create the global metrics collector instance.

    Returns:
        Global MetricsCollector instance

    Example:
        >>> metrics = get_metrics_collector()
        >>> metrics.record_api_call("claude", 1500, 250.5, True)
    """
    global _global_metrics

    if _global_metrics is None:
        with _global_metrics_lock:
            if _global_metrics is None:
                _global_metrics = MetricsCollector()

    return _global_metrics
