from prometheus_client import Counter, Gauge


class Metrics:
    REQUEST_COUNT = Counter(
        'request_count', 'App Request Count', ['app_name', 'route', 'environment']
    )

    REQUEST_LATENCY = Gauge('request_latency_seconds', 'Request latency',
                            ['app_name', 'route', 'environment']
                            )

    LOGIN_SUCCESS = Counter('login_count_success', 'Login Success Count',
                            ['status_code', 'environment']
                            )

    LOGIN_FAILURE = Counter('login_count_failure', 'Login Failure Count',
                            ['status_code', 'environment']
                            )

    def __init__(self, app_name, environment):
        self.name = app_name
        self.env = environment

    def count_requests(self, route):
        Metrics.REQUEST_COUNT.labels(self.name, route, self.env).inc()

    def request_latency(self, route, total_in_seconds):
        Metrics.REQUEST_LATENCY.labels(self.name, route, self.env).set(
            total_in_seconds
        )


