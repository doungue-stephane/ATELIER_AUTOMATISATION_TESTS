import time
import requests

class HttpClient:
    def __init__(self, timeout_s=3, max_retry=1):
        self.timeout_s = timeout_s
        self.max_retry = max_retry

    def get(self, url, params=None):
        last_err = None
        for attempt in range(self.max_retry + 1):
            try:
                t0 = time.perf_counter()
                resp = requests.get(url, params=params, timeout=self.timeout_s)
                latency_ms = (time.perf_counter() - t0) * 1000.0

                if resp.status_code == 429 and attempt < self.max_retry:
                    time.sleep(1.0)
                    continue
                if 500 <= resp.status_code <= 599 and attempt < self.max_retry:
                    time.sleep(0.5)
                    continue

                return resp, latency_ms, None

            except requests.RequestException as e:
                last_err = str(e)
                if attempt < self.max_retry:
                    time.sleep(0.5)
                    continue

        return None, None, last_err