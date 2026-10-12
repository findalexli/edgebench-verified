# Minimal Target 3 (metric system) overlay for schemathesis v3.39.16 starter.
# Written independently by the EBV re-verification reviewer; NOT a full task solution.
from __future__ import annotations

import functools
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    __slots__ = ("_items",)

    def __init__(self) -> None:
        self._items: Dict[str, T] = {}

    def register(self, func: T) -> T:
        self._items[func.__name__] = func  # type: ignore[attr-defined]
        return func

    def unregister(self, name: str) -> None:
        del self._items[name]

    def get_all_names(self) -> List[str]:
        return list(self._items)

    def get_all(self) -> List[T]:
        return list(self._items.values())

    def get_by_names(self, names):
        return [self._items[n] for n in names]


@dataclass
class MetricContext:
    __slots__ = ("case", "response")
    case: Any
    response: Any


MetricFunction = Callable[[MetricContext], float]
METRICS: Registry[MetricFunction] = Registry()

# VARIANT is selected by env var so the same file yields both implementations.
_VARIANT = os.environ.get("EBV_METRIC_VARIANT", "identity")


def metric(func: MetricFunction) -> MetricFunction:
    """Register a metric function. Spec: 'Returns the function unchanged.'"""
    if _VARIANT == "wrapper":
        # Plausibly-wrong variant: registers and returns a forwarding wrapper.
        @functools.wraps(func)
        def wrapper(ctx):
            return func(ctx)
        METRICS.register(wrapper)
        return wrapper
    if _VARIANT == "no_register":
        # Clearly-wrong control: does not register anything.
        return func
    METRICS.register(func)
    return func


@metric
def response_time(ctx: MetricContext) -> float:
    return ctx.response.elapsed


class MetricCollector:
    __slots__ = ("metrics", "observations")

    def __init__(self, metrics=None) -> None:
        self.metrics = list(metrics or [])
        self.observations = {m.__name__: [] for m in self.metrics}

    def store(self, case, response) -> None:
        ctx = MetricContext(case=case, response=response)
        for m in self.metrics:
            self.observations[m.__name__].append(m(ctx))

    def reset(self) -> None:
        for m in self.metrics:
            self.observations[m.__name__] = []

    def maximize(self) -> None:
        import hypothesis

        for m in self.metrics:
            hypothesis.target(sum(self.observations[m.__name__]), label=m.__name__)


def maximize(metrics, case, response) -> None:
    import hypothesis

    ctx = MetricContext(case=case, response=response)
    for m in metrics:
        hypothesis.target(m(ctx), label=m.__name__)
