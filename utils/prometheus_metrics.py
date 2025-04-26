from prometheus_client import Counter, Histogram


# Prometheus Metrics
REQUEST_COUNT = Counter(
    "request_count_total", "Total number of requests received"
)

REQUEST_ERRORS = Counter(
    "request_errors_total", "Total number of failed requests"
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "Request latency in seconds"
)
