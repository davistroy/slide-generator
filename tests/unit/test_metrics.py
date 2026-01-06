"""
Unit tests for metrics module.

Tests cover:
- Counter, Gauge, and Histogram metric types
- MetricsCollector class
- API call tracking
- Thread safety
- Prometheus export format
- Global metrics instance
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from plugin.lib.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_metrics_collector,
)


class TestCounter:
    """Tests for Counter metric class."""

    def test_initialization(self):
        """Test counter initializes to zero."""
        counter = Counter()
        assert counter.value == 0
        assert counter.get() == 0

    def test_increment_default(self):
        """Test incrementing counter by default amount (1)."""
        counter = Counter()
        counter.increment()
        assert counter.get() == 1

    def test_increment_custom_amount(self):
        """Test incrementing counter by custom amount."""
        counter = Counter()
        counter.increment(5)
        assert counter.get() == 5
        counter.increment(10)
        assert counter.get() == 15

    def test_increment_zero(self):
        """Test incrementing counter by zero."""
        counter = Counter()
        counter.increment(0)
        assert counter.get() == 0

    def test_increment_negative(self):
        """Test incrementing counter by negative value (allowed but unusual)."""
        counter = Counter()
        counter.increment(-5)
        assert counter.get() == -5

    def test_reset(self):
        """Test resetting counter to zero."""
        counter = Counter()
        counter.increment(100)
        assert counter.get() == 100
        counter.reset()
        assert counter.get() == 0

    def test_thread_safety(self):
        """Test counter is thread-safe."""
        counter = Counter()
        num_threads = 10
        increments_per_thread = 100

        def increment_counter():
            for _ in range(increments_per_thread):
                counter.increment()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(increment_counter) for _ in range(num_threads)]
            for future in futures:
                future.result()

        assert counter.get() == num_threads * increments_per_thread

    def test_initial_value_custom(self):
        """Test counter with custom initial value."""
        counter = Counter(value=50)
        assert counter.get() == 50


class TestGauge:
    """Tests for Gauge metric class."""

    def test_initialization(self):
        """Test gauge initializes to zero."""
        gauge = Gauge()
        assert gauge.value == 0.0
        assert gauge.get() == 0.0

    def test_set_value(self):
        """Test setting gauge value."""
        gauge = Gauge()
        gauge.set(42.5)
        assert gauge.get() == 42.5

    def test_set_negative_value(self):
        """Test setting gauge to negative value."""
        gauge = Gauge()
        gauge.set(-10.5)
        assert gauge.get() == -10.5

    def test_increment_default(self):
        """Test incrementing gauge by default amount (1.0)."""
        gauge = Gauge()
        gauge.increment()
        assert gauge.get() == 1.0

    def test_increment_custom_amount(self):
        """Test incrementing gauge by custom amount."""
        gauge = Gauge()
        gauge.set(5.0)
        gauge.increment(2.5)
        assert gauge.get() == 7.5

    def test_decrement_default(self):
        """Test decrementing gauge by default amount (1.0)."""
        gauge = Gauge()
        gauge.set(5.0)
        gauge.decrement()
        assert gauge.get() == 4.0

    def test_decrement_custom_amount(self):
        """Test decrementing gauge by custom amount."""
        gauge = Gauge()
        gauge.set(10.0)
        gauge.decrement(3.5)
        assert gauge.get() == 6.5

    def test_decrement_to_negative(self):
        """Test decrementing gauge to negative value."""
        gauge = Gauge()
        gauge.decrement(5.0)
        assert gauge.get() == -5.0

    def test_reset(self):
        """Test resetting gauge to zero."""
        gauge = Gauge()
        gauge.set(100.0)
        gauge.reset()
        assert gauge.get() == 0.0

    def test_thread_safety(self):
        """Test gauge is thread-safe."""
        gauge = Gauge()
        num_threads = 10
        operations_per_thread = 50

        def modify_gauge():
            for _ in range(operations_per_thread):
                gauge.increment(1.0)
                gauge.decrement(0.5)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(modify_gauge) for _ in range(num_threads)]
            for future in futures:
                future.result()

        # Each thread does +1.0, -0.5 = +0.5 per iteration
        expected = num_threads * operations_per_thread * 0.5
        assert gauge.get() == expected

    def test_initial_value_custom(self):
        """Test gauge with custom initial value."""
        gauge = Gauge(value=25.5)
        assert gauge.get() == 25.5


class TestHistogram:
    """Tests for Histogram metric class."""

    def test_initialization(self):
        """Test histogram initializes with empty values."""
        histogram = Histogram()
        assert histogram.values == []

    def test_observe_single_value(self):
        """Test observing a single value."""
        histogram = Histogram()
        histogram.observe(10.0)
        assert histogram.values == [10.0]

    def test_observe_multiple_values(self):
        """Test observing multiple values."""
        histogram = Histogram()
        histogram.observe(10.0)
        histogram.observe(20.0)
        histogram.observe(30.0)
        assert histogram.values == [10.0, 20.0, 30.0]

    def test_get_stats_empty(self):
        """Test statistics for empty histogram."""
        histogram = Histogram()
        stats = histogram.get_stats()

        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["mean"] == 0.0
        assert stats["median"] == 0.0
        assert stats["p95"] == 0.0
        assert stats["p99"] == 0.0
        assert stats["count"] == 0

    def test_get_stats_single_value(self):
        """Test statistics for histogram with single value."""
        histogram = Histogram()
        histogram.observe(42.0)
        stats = histogram.get_stats()

        assert stats["min"] == 42.0
        assert stats["max"] == 42.0
        assert stats["mean"] == 42.0
        assert stats["median"] == 42.0
        assert stats["count"] == 1

    def test_get_stats_multiple_values(self):
        """Test statistics for histogram with multiple values."""
        histogram = Histogram()
        for value in [10.0, 20.0, 30.0, 40.0, 50.0]:
            histogram.observe(value)

        stats = histogram.get_stats()

        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["mean"] == 30.0
        assert stats["median"] == 30.0
        assert stats["count"] == 5

    def test_get_stats_percentiles(self):
        """Test percentile calculations."""
        histogram = Histogram()
        # Add 100 values: 1, 2, 3, ..., 100
        for i in range(1, 101):
            histogram.observe(float(i))

        stats = histogram.get_stats()

        assert stats["count"] == 100
        assert stats["min"] == 1.0
        assert stats["max"] == 100.0
        # p95 should be around index 95 (value 96 since 0-indexed becomes 95*100/100)
        assert stats["p95"] == 96.0
        # p99 should be around index 99
        assert stats["p99"] == 100.0

    def test_reset(self):
        """Test resetting histogram."""
        histogram = Histogram()
        histogram.observe(10.0)
        histogram.observe(20.0)
        histogram.reset()

        assert histogram.values == []
        stats = histogram.get_stats()
        assert stats["count"] == 0

    def test_thread_safety(self):
        """Test histogram is thread-safe."""
        histogram = Histogram()
        num_threads = 10
        observations_per_thread = 100

        def observe_values():
            for i in range(observations_per_thread):
                histogram.observe(float(i))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(observe_values) for _ in range(num_threads)]
            for future in futures:
                future.result()

        stats = histogram.get_stats()
        assert stats["count"] == num_threads * observations_per_thread

    def test_negative_values(self):
        """Test histogram with negative values."""
        histogram = Histogram()
        histogram.observe(-10.0)
        histogram.observe(0.0)
        histogram.observe(10.0)

        stats = histogram.get_stats()
        assert stats["min"] == -10.0
        assert stats["max"] == 10.0
        assert stats["mean"] == 0.0


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_initialization(self):
        """Test collector initializes with standard metrics."""
        collector = MetricsCollector()

        assert isinstance(collector.start_time, datetime)
        assert collector.lock is not None

        # Check standard counters exist
        assert "api_calls_total" in collector.counters
        assert "api_calls_success" in collector.counters
        assert "api_calls_error" in collector.counters
        assert "tokens_input_total" in collector.counters
        assert "tokens_output_total" in collector.counters
        assert "tokens_total" in collector.counters
        assert "errors_total" in collector.counters

        # Check standard histogram exists
        assert "api_latency_ms" in collector.histograms

    def test_record_api_call_success(self):
        """Test recording successful API call."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude",
            tokens=1500,
            latency_ms=250.5,
            success=True,
        )

        assert collector.get_counter("api_calls_total") == 1
        assert collector.get_counter("api_calls_success") == 1
        assert collector.get_counter("api_calls_error") == 0
        assert collector.get_counter("api_calls_claude_total") == 1
        assert collector.get_counter("api_calls_claude_success") == 1
        assert collector.get_counter("tokens_total") == 1500
        assert collector.get_counter("tokens_claude_total") == 1500

        latency_stats = collector.get_histogram_stats("api_latency_ms")
        assert latency_stats["count"] == 1
        assert latency_stats["mean"] == 250.5

    def test_record_api_call_failure(self):
        """Test recording failed API call."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="gemini",
            tokens=500,
            latency_ms=100.0,
            success=False,
        )

        assert collector.get_counter("api_calls_total") == 1
        assert collector.get_counter("api_calls_success") == 0
        assert collector.get_counter("api_calls_error") == 1
        assert collector.get_counter("api_calls_gemini_total") == 1
        assert collector.get_counter("api_calls_gemini_error") == 1

    def test_record_api_call_with_input_output_tokens(self):
        """Test recording API call with separate input/output token counts."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude",
            tokens=1500,
            latency_ms=250.0,
            success=True,
            input_tokens=1000,
            output_tokens=500,
        )

        assert collector.get_counter("tokens_total") == 1500
        assert collector.get_counter("tokens_input_total") == 1000
        assert collector.get_counter("tokens_output_total") == 500
        assert collector.get_counter("tokens_claude_input") == 1000
        assert collector.get_counter("tokens_claude_output") == 500

    def test_record_api_call_without_input_output_tokens(self):
        """Test recording API call without separate token counts."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude",
            tokens=1500,
            latency_ms=250.0,
            success=True,
        )

        assert collector.get_counter("tokens_total") == 1500
        # Input/output should remain at 0 since not provided
        assert collector.get_counter("tokens_input_total") == 0
        assert collector.get_counter("tokens_output_total") == 0

    def test_record_multiple_api_calls(self):
        """Test recording multiple API calls."""
        collector = MetricsCollector()

        for i in range(5):
            collector.record_api_call(
                provider="claude",
                tokens=100 * (i + 1),
                latency_ms=50.0 * (i + 1),
                success=True,
            )

        assert collector.get_counter("api_calls_total") == 5
        assert collector.get_counter("tokens_total") == 100 + 200 + 300 + 400 + 500

        latency_stats = collector.get_histogram_stats("api_latency_ms")
        assert latency_stats["count"] == 5

    def test_record_api_calls_multiple_providers(self):
        """Test recording API calls from different providers."""
        collector = MetricsCollector()

        collector.record_api_call("claude", 1000, 200.0, True)
        collector.record_api_call("gemini", 500, 150.0, True)
        collector.record_api_call("claude", 800, 180.0, False)

        assert collector.get_counter("api_calls_total") == 3
        assert collector.get_counter("api_calls_claude_total") == 2
        assert collector.get_counter("api_calls_gemini_total") == 1
        assert collector.get_counter("api_calls_claude_success") == 1
        assert collector.get_counter("api_calls_claude_error") == 1
        assert collector.get_counter("api_calls_gemini_success") == 1

    def test_increment_counter(self):
        """Test incrementing custom counter."""
        collector = MetricsCollector()

        collector.increment_counter("slides_generated")
        assert collector.get_counter("slides_generated") == 1

        collector.increment_counter("slides_generated", 5)
        assert collector.get_counter("slides_generated") == 6

    def test_set_gauge(self):
        """Test setting gauge value."""
        collector = MetricsCollector()

        collector.set_gauge("active_requests", 5.0)
        assert collector.get_gauge("active_requests") == 5.0

        collector.set_gauge("active_requests", 3.0)
        assert collector.get_gauge("active_requests") == 3.0

    def test_increment_gauge(self):
        """Test incrementing gauge."""
        collector = MetricsCollector()

        collector.increment_gauge("queue_size", 2.0)
        assert collector.get_gauge("queue_size") == 2.0

        collector.increment_gauge("queue_size")
        assert collector.get_gauge("queue_size") == 3.0

    def test_decrement_gauge(self):
        """Test decrementing gauge."""
        collector = MetricsCollector()

        collector.set_gauge("queue_size", 10.0)
        collector.decrement_gauge("queue_size", 3.0)
        assert collector.get_gauge("queue_size") == 7.0

        collector.decrement_gauge("queue_size")
        assert collector.get_gauge("queue_size") == 6.0

    def test_observe_histogram(self):
        """Test observing histogram values."""
        collector = MetricsCollector()

        collector.observe_histogram("processing_time_ms", 100.0)
        collector.observe_histogram("processing_time_ms", 200.0)
        collector.observe_histogram("processing_time_ms", 300.0)

        stats = collector.get_histogram_stats("processing_time_ms")
        assert stats["count"] == 3
        assert stats["mean"] == 200.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0

    def test_record_error(self):
        """Test recording errors."""
        collector = MetricsCollector()

        collector.record_error("api_timeout")
        collector.record_error("api_timeout")
        collector.record_error("validation_error")

        assert collector.get_counter("errors_total") == 3
        assert collector.get_counter("errors_api_timeout") == 2
        assert collector.get_counter("errors_validation_error") == 1

    def test_get_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector()

        collector.record_api_call("claude", 1000, 200.0, True)
        collector.set_gauge("active_requests", 5.0)
        collector.observe_histogram("custom_histogram", 100.0)

        summary = collector.get_summary()

        assert "start_time" in summary
        assert "uptime_seconds" in summary
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary

        assert summary["counters"]["api_calls_total"] == 1
        assert summary["gauges"]["active_requests"] == 5.0
        assert "custom_histogram" in summary["histograms"]

    def test_get_summary_uptime(self):
        """Test that uptime increases over time."""
        collector = MetricsCollector()

        summary1 = collector.get_summary()
        time.sleep(0.1)
        summary2 = collector.get_summary()

        assert summary2["uptime_seconds"] > summary1["uptime_seconds"]

    def test_export_prometheus_counters(self):
        """Test Prometheus export format for counters."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter", 42)

        output = collector.export_prometheus()

        assert "# HELP test_counter Counter metric" in output
        assert "# TYPE test_counter counter" in output
        assert "test_counter 42" in output

    def test_export_prometheus_gauges(self):
        """Test Prometheus export format for gauges."""
        collector = MetricsCollector()
        collector.set_gauge("test_gauge", 3.14)

        output = collector.export_prometheus()

        assert "# HELP test_gauge Gauge metric" in output
        assert "# TYPE test_gauge gauge" in output
        assert "test_gauge 3.14" in output

    def test_export_prometheus_histograms(self):
        """Test Prometheus export format for histograms."""
        collector = MetricsCollector()
        for i in range(100):
            collector.observe_histogram("test_histogram", float(i))

        output = collector.export_prometheus()

        assert "# HELP test_histogram Histogram metric" in output
        assert "# TYPE test_histogram summary" in output
        assert 'test_histogram{quantile="0.5"}' in output
        assert 'test_histogram{quantile="0.95"}' in output
        assert 'test_histogram{quantile="0.99"}' in output
        assert "test_histogram_sum" in output
        assert "test_histogram_count 100" in output

    def test_export_prometheus_empty_histogram(self):
        """Test Prometheus export format for empty histogram."""
        collector = MetricsCollector()

        output = collector.export_prometheus()

        # Standard histogram should exist but be empty
        assert "api_latency_ms" in output
        assert "api_latency_ms_count 0" in output

    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()

        collector.record_api_call("claude", 1000, 200.0, True)
        collector.set_gauge("active_requests", 5.0)
        collector.observe_histogram("custom_histogram", 100.0)

        collector.reset()

        assert collector.get_counter("api_calls_total") == 0
        assert collector.get_gauge("active_requests") == 0.0
        assert collector.get_histogram_stats("custom_histogram")["count"] == 0

    def test_reset_updates_start_time(self):
        """Test that reset updates start time."""
        collector = MetricsCollector()
        original_start_time = collector.start_time

        time.sleep(0.1)
        collector.reset()

        assert collector.start_time > original_start_time

    def test_get_counter_nonexistent(self):
        """Test getting nonexistent counter creates it with zero value."""
        collector = MetricsCollector()

        # Getting a nonexistent counter should create it via defaultdict
        value = collector.get_counter("nonexistent_counter")
        assert value == 0

    def test_get_gauge_nonexistent(self):
        """Test getting nonexistent gauge creates it with zero value."""
        collector = MetricsCollector()

        value = collector.get_gauge("nonexistent_gauge")
        assert value == 0.0

    def test_get_histogram_stats_nonexistent(self):
        """Test getting stats for nonexistent histogram."""
        collector = MetricsCollector()

        stats = collector.get_histogram_stats("nonexistent_histogram")
        assert stats["count"] == 0

    def test_thread_safety_api_calls(self):
        """Test thread safety of API call recording."""
        collector = MetricsCollector()
        num_threads = 10
        calls_per_thread = 100

        def record_calls():
            for _ in range(calls_per_thread):
                collector.record_api_call(
                    provider="claude",
                    tokens=100,
                    latency_ms=50.0,
                    success=True,
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_calls) for _ in range(num_threads)]
            for future in futures:
                future.result()

        assert collector.get_counter("api_calls_total") == num_threads * calls_per_thread
        assert (
            collector.get_counter("tokens_total") == num_threads * calls_per_thread * 100
        )

    def test_thread_safety_mixed_operations(self):
        """Test thread safety with mixed metric operations."""
        collector = MetricsCollector()
        num_threads = 5
        operations_per_thread = 50

        def mixed_operations():
            for i in range(operations_per_thread):
                collector.increment_counter("mixed_counter")
                collector.set_gauge("mixed_gauge", float(i))
                collector.observe_histogram("mixed_histogram", float(i))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mixed_operations) for _ in range(num_threads)]
            for future in futures:
                future.result()

        assert (
            collector.get_counter("mixed_counter")
            == num_threads * operations_per_thread
        )
        histogram_stats = collector.get_histogram_stats("mixed_histogram")
        assert histogram_stats["count"] == num_threads * operations_per_thread


class TestGetMetricsCollector:
    """Tests for global metrics collector function."""

    def test_returns_metrics_collector(self):
        """Test that function returns a MetricsCollector instance."""
        # Reset global state for clean test
        import plugin.lib.metrics as metrics_module

        metrics_module._global_metrics = None

        collector = get_metrics_collector()
        assert isinstance(collector, MetricsCollector)

    def test_returns_same_instance(self):
        """Test that function returns the same instance (singleton)."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_thread_safe_initialization(self):
        """Test thread-safe initialization of global collector."""
        import plugin.lib.metrics as metrics_module

        metrics_module._global_metrics = None

        collectors = []
        lock = threading.Lock()

        def get_collector():
            collector = get_metrics_collector()
            with lock:
                collectors.append(collector)

        threads = [threading.Thread(target=get_collector) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should have received the same instance
        assert all(c is collectors[0] for c in collectors)

    def test_global_collector_persists_data(self):
        """Test that global collector persists data across calls."""
        collector1 = get_metrics_collector()
        collector1.increment_counter("global_test_counter", 42)

        collector2 = get_metrics_collector()
        assert collector2.get_counter("global_test_counter") == 42


class TestMetricsCollectorEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_large_token_counts(self):
        """Test handling of large token counts."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude",
            tokens=10_000_000,
            latency_ms=5000.0,
            success=True,
            input_tokens=8_000_000,
            output_tokens=2_000_000,
        )

        assert collector.get_counter("tokens_total") == 10_000_000
        assert collector.get_counter("tokens_input_total") == 8_000_000
        assert collector.get_counter("tokens_output_total") == 2_000_000

    def test_very_small_latency(self):
        """Test handling of very small latency values."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude",
            tokens=100,
            latency_ms=0.001,
            success=True,
        )

        stats = collector.get_histogram_stats("api_latency_ms")
        assert stats["min"] == 0.001

    def test_zero_tokens(self):
        """Test handling of zero token count."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude",
            tokens=0,
            latency_ms=50.0,
            success=True,
        )

        assert collector.get_counter("tokens_total") == 0
        assert collector.get_counter("api_calls_total") == 1

    def test_special_provider_names(self):
        """Test handling of special characters in provider names."""
        collector = MetricsCollector()

        collector.record_api_call(
            provider="claude_v2",
            tokens=100,
            latency_ms=50.0,
            success=True,
        )

        assert collector.get_counter("api_calls_claude_v2_total") == 1

    def test_special_error_types(self):
        """Test handling of special characters in error types."""
        collector = MetricsCollector()

        collector.record_error("rate_limit_exceeded")
        collector.record_error("connection_timeout")
        collector.record_error("invalid_api_key")

        assert collector.get_counter("errors_rate_limit_exceeded") == 1
        assert collector.get_counter("errors_connection_timeout") == 1
        assert collector.get_counter("errors_invalid_api_key") == 1

    def test_prometheus_export_structure(self):
        """Test Prometheus export has correct structure."""
        collector = MetricsCollector()
        collector.record_api_call("test", 100, 50.0, True)

        output = collector.export_prometheus()
        lines = output.strip().split("\n")

        # Each metric should have HELP, TYPE, and value lines
        # Verify structure by checking for expected patterns
        help_lines = [l for l in lines if l.startswith("# HELP")]
        type_lines = [l for l in lines if l.startswith("# TYPE")]

        assert len(help_lines) > 0
        assert len(type_lines) > 0
        assert len(help_lines) == len(type_lines)

    def test_summary_start_time_format(self):
        """Test that start_time in summary is ISO format."""
        collector = MetricsCollector()
        summary = collector.get_summary()

        # Should be parseable as ISO format
        start_time = summary["start_time"]
        parsed = datetime.fromisoformat(start_time)
        assert isinstance(parsed, datetime)

    def test_histogram_percentile_edge_case_small_dataset(self):
        """Test percentile calculation with small dataset."""
        histogram = Histogram()
        histogram.observe(1.0)
        histogram.observe(2.0)
        histogram.observe(3.0)

        stats = histogram.get_stats()
        # With 3 values, p95 index = int(3 * 0.95) = int(2.85) = 2
        # So p95 should be the 3rd value (index 2) = 3.0
        assert stats["p95"] == 3.0

    def test_histogram_float_precision(self):
        """Test histogram handles float precision correctly."""
        histogram = Histogram()
        histogram.observe(0.1)
        histogram.observe(0.2)
        histogram.observe(0.3)

        stats = histogram.get_stats()
        # Mean should be 0.2, but due to float precision may be slightly off
        assert abs(stats["mean"] - 0.2) < 0.0001

    def test_multiple_resets(self):
        """Test multiple consecutive resets."""
        collector = MetricsCollector()

        collector.record_api_call("claude", 100, 50.0, True)
        collector.reset()
        collector.reset()
        collector.reset()

        assert collector.get_counter("api_calls_total") == 0

    def test_operations_after_reset(self):
        """Test that operations work correctly after reset."""
        collector = MetricsCollector()

        collector.record_api_call("claude", 100, 50.0, True)
        collector.reset()

        collector.record_api_call("claude", 200, 75.0, True)

        assert collector.get_counter("api_calls_total") == 1
        assert collector.get_counter("tokens_total") == 200
