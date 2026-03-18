import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse


@dataclass
class EndpointMetric:
    count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0


class InMemoryMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics: Dict[str, EndpointMetric] = defaultdict(EndpointMetric)

    def observe(self, route: str, status_code: int, latency_ms: float) -> None:
        with self._lock:
            record = self._metrics[route]
            record.count += 1
            record.total_latency_ms += latency_ms
            if status_code >= 400:
                record.error_count += 1

    def render_prometheus(self) -> str:
        lines = [
            "# HELP app_requests_total Total HTTP requests per route",
            "# TYPE app_requests_total counter",
            "# HELP app_request_errors_total Total HTTP error responses per route",
            "# TYPE app_request_errors_total counter",
            "# HELP app_request_latency_avg_ms Average request latency in milliseconds per route",
            "# TYPE app_request_latency_avg_ms gauge",
        ]
        with self._lock:
            for route, metric in self._metrics.items():
                safe_route = route.replace('"', "")
                avg_latency = metric.total_latency_ms / metric.count if metric.count else 0.0
                lines.append(f'app_requests_total{{route="{safe_route}"}} {metric.count}')
                lines.append(f'app_request_errors_total{{route="{safe_route}"}} {metric.error_count}')
                lines.append(f'app_request_latency_avg_ms{{route="{safe_route}"}} {avg_latency:.2f}')
        return "\n".join(lines) + "\n"


metrics = InMemoryMetrics()
metrics_router = APIRouter()


@metrics_router.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint() -> str:
    return metrics.render_prometheus()


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    route = request.url.path
    metrics.observe(route=route, status_code=response.status_code, latency_ms=duration_ms)
    return response
