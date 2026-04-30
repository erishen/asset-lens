"""
Prometheus Metrics - 监控指标模块
提供 Prometheus 兼容的监控指标
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """指标值"""

    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """计数器指标 - 只增不减"""

    def __init__(self, name: str, description: str, labels: list[str] | None = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[str, float] = {}
        self._lock = Lock()

    def _make_key(self, labels: dict[str, str] | None = None) -> str:
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """增加计数"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def collect(self) -> list[MetricValue]:
        """收集指标"""
        with self._lock:
            return [
                MetricValue(value=v, labels=dict(pair.split("=") for pair in k.split(",") if "=" in k) if k else {})
                for k, v in self._values.items()
            ]

    def export(self) -> str:
        """导出 Prometheus 格式"""
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} counter"]
        for metric in self.collect():
            if metric.labels:
                label_str = "{" + ",".join(f'{k}="{v}"' for k, v in metric.labels.items()) + "}"
                lines.append(f"{self.name}{label_str} {metric.value}")
            else:
                lines.append(f"{self.name} {metric.value}")
        return "\n".join(lines)


class Gauge:
    """仪表指标 - 可增可减"""

    def __init__(self, name: str, description: str, labels: list[str] | None = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[str, float] = {}
        self._lock = Lock()

    def _make_key(self, labels: dict[str, str] | None = None) -> str:
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """设置值"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = value

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """增加值"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def dec(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """减少值"""
        key = self._make_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) - value

    def collect(self) -> list[MetricValue]:
        """收集指标"""
        with self._lock:
            return [
                MetricValue(value=v, labels=dict(pair.split("=") for pair in k.split(",") if "=" in k) if k else {})
                for k, v in self._values.items()
            ]

    def export(self) -> str:
        """导出 Prometheus 格式"""
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} gauge"]
        for metric in self.collect():
            if metric.labels:
                label_str = "{" + ",".join(f'{k}="{v}"' for k, v in metric.labels.items()) + "}"
                lines.append(f"{self.name}{label_str} {metric.value}")
            else:
                lines.append(f"{self.name} {metric.value}")
        return "\n".join(lines)


class Histogram:
    """直方图指标"""

    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(
        self,
        name: str,
        description: str,
        buckets: list[float] | None = None,
        labels: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self.label_names = labels or []
        self._counts: dict[str, list[int]] = {}
        self._sums: dict[str, float] = {}
        self._lock = Lock()

    def _make_key(self, labels: dict[str, str] | None = None) -> str:
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """记录观察值"""
        key = self._make_key(labels)
        with self._lock:
            if key not in self._counts:
                self._counts[key] = [0] * (len(self.buckets) + 1)
                self._sums[key] = 0.0

            for i, bucket in enumerate(self.buckets):
                if value <= bucket:
                    self._counts[key][i] += 1
                    break
            else:
                self._counts[key][-1] += 1

            self._sums[key] += value

    def export(self) -> str:
        """导出 Prometheus 格式"""
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} histogram"]

        with self._lock:
            for key, counts in self._counts.items():
                labels = dict(pair.split("=") for pair in key.split(",") if "=" in pair) if key else {}
                label_str = "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}" if labels else ""

                cumulative = 0
                for i, bucket in enumerate(self.buckets):
                    cumulative += counts[i]
                    bucket_label = f'{{le="{bucket}"'
                    if labels:
                        bucket_label = "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + f',le="{bucket}"}}'
                    else:
                        bucket_label = f'{{le="{bucket}"}}'
                    lines.append(f"{self.name}_bucket{bucket_label} {cumulative}")

                cumulative += counts[-1]
                inf_label = (
                    '{le="+Inf"}'
                    if not labels
                    else "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + ',le="+Inf"}'
                )
                lines.append(f"{self.name}_bucket{inf_label} {cumulative}")
                lines.append(f"{self.name}_sum{label_str} {self._sums[key]}")
                lines.append(f"{self.name}_count{label_str} {cumulative}")

        return "\n".join(lines)


class MetricsRegistry:
    """指标注册中心"""

    def __init__(self):
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}
        self._lock = Lock()

    def register(self, metric: Counter | Gauge | Histogram) -> None:
        """注册指标"""
        with self._lock:
            self._metrics[metric.name] = metric

    def get(self, name: str) -> Counter | Gauge | Histogram | None:
        """获取指标"""
        return self._metrics.get(name)

    def export(self) -> str:
        """导出所有指标"""
        with self._lock:
            return "\n\n".join(m.export() for m in self._metrics.values())


metrics_registry = MetricsRegistry()


def timer(metric: Histogram) -> Callable:
    """计时装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metric.observe(duration)

        return wrapper

    return decorator


async def async_timer(metric: Histogram) -> Callable:
    """异步计时装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                metric.observe(duration)

        return wrapper

    return decorator


__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsRegistry",
    "metrics_registry",
    "timer",
    "async_timer",
]
