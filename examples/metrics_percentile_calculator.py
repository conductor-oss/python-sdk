#!/usr/bin/env python3
"""
Utility to calculate percentiles from Prometheus histogram metrics.

This script reads histogram metrics from the Prometheus metrics file and
calculates percentiles (p50, p75, p90, p95, p99) for timing metrics.

Usage:
    python3 metrics_percentile_calculator.py /path/to/metrics.prom

Example output:
    task_poll_time_seconds (taskType="email_service", status="SUCCESS"):
      Count: 100
      p50: 15.2ms
      p75: 23.4ms
      p90: 35.1ms
      p95: 45.2ms
      p99: 98.5ms
"""

import sys
import re
from typing import Dict, List, Tuple


def parse_histogram_metrics(file_path: str) -> Dict[str, List[Tuple[float, float]]]:
    """
    Parse histogram bucket data from Prometheus metrics file.

    Returns:
        Dict mapping metric_name+labels to list of (bucket_le, count) tuples
    """
    histograms = {}

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse bucket lines: metric_name_bucket{labels,le="0.05"} count
            if '_bucket{' in line:
                match = re.match(r'([a-z_]+)_bucket\{([^}]+)\}\s+([0-9.]+)', line)
                if match:
                    metric_name = match.group(1)
                    labels_str = match.group(2)
                    count = float(match.group(3))

                    # Extract le value and other labels
                    le_match = re.search(r'le="([^"]+)"', labels_str)
                    if le_match:
                        le_value = le_match.group(1)
                        if le_value == '+Inf':
                            le_value = float('inf')
                        else:
                            le_value = float(le_value)

                        # Remove le from labels for grouping
                        other_labels = re.sub(r',?le="[^"]+"', '', labels_str)
                        other_labels = re.sub(r'le="[^"]+",?', '', other_labels)

                        key = f"{metric_name}{{{other_labels}}}"
                        if key not in histograms:
                            histograms[key] = []
                        histograms[key].append((le_value, count))

    # Sort buckets by le value
    for key in histograms:
        histograms[key].sort(key=lambda x: x[0])

    return histograms


def calculate_percentile(buckets: List[Tuple[float, float]], percentile: float) -> float:
    """
    Calculate percentile from histogram buckets using linear interpolation.

    Args:
        buckets: List of (upper_bound, cumulative_count) tuples
        percentile: Percentile to calculate (0.0 to 1.0)

    Returns:
        Estimated percentile value in seconds
    """
    if not buckets:
        return 0.0

    total_count = buckets[-1][1]  # Total is the +Inf bucket count
    if total_count == 0:
        return 0.0

    target_count = total_count * percentile

    # Find the bucket containing the target percentile
    prev_le = 0.0
    prev_count = 0.0

    for le, count in buckets:
        if count >= target_count:
            # Linear interpolation within the bucket
            if count == prev_count:
                return prev_le

            # Calculate position within bucket
            bucket_fraction = (target_count - prev_count) / (count - prev_count)
            bucket_width = le - prev_le if le != float('inf') else 0

            return prev_le + (bucket_fraction * bucket_width)

        prev_le = le
        prev_count = count

    return prev_le


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 metrics_percentile_calculator.py <metrics_file>")
        print("\nExample:")
        print("  python3 metrics_percentile_calculator.py /tmp/conductor_metrics/conductor_metrics.prom")
        sys.exit(1)

    metrics_file = sys.argv[1]

    try:
        histograms = parse_histogram_metrics(metrics_file)
    except FileNotFoundError:
        print(f"Error: Metrics file not found: {metrics_file}")
        sys.exit(1)

    if not histograms:
        print("No histogram metrics found in file")
        sys.exit(0)

    print("=" * 80)
    print("Histogram Percentiles")
    print("=" * 80)

    # Calculate percentiles for each histogram
    for metric_labels, buckets in sorted(histograms.items()):
        if not buckets:
            continue

        total_count = buckets[-1][1]
        if total_count == 0:
            continue

        print(f"\n{metric_labels}:")
        print(f"  Count: {int(total_count)}")

        # Calculate key percentiles
        for p_name, p_value in [('p50', 0.50), ('p75', 0.75), ('p90', 0.90), ('p95', 0.95), ('p99', 0.99)]:
            percentile_seconds = calculate_percentile(buckets, p_value)
            percentile_ms = percentile_seconds * 1000
            print(f"  {p_name}: {percentile_ms:.2f}ms")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
