import datetime
import statistics
from tester.client import HttpClient
from tester import tests as t

def p95(values):
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(0.95 * (len(s) - 1))
    return float(s[idx])

def run_suite(api_name="Frankfurter", base_url="https://api.frankfurter.app"):
    client = HttpClient(timeout_s=3, max_retry=1)

    test_fns = [
        t.test_200_latest_eur_usd,
        t.test_content_type_json,
        t.test_json_parse,
        t.test_required_fields,
        t.test_types_and_date_format,
        t.test_rate_usd_present_and_numeric,
        t.test_invalid_currency_returns_4xx,
    ]

    results = []
    latencies = []

    for fn in test_fns:
        r = fn(client, base_url)
        status = "PASS" if r["ok"] else "FAIL"
        results.append({
            "name": r["name"],
            "status": status,
            "latency_ms": r.get("latency_ms"),
            "details": r.get("details", "")
        })
        if r.get("latency_ms") is not None:
            latencies.append(float(r["latency_ms"]))

    passed = sum(1 for x in results if x["status"] == "PASS")
    failed = len(results) - passed
    error_rate = failed / max(1, len(results))

    latency_avg = statistics.mean(latencies) if latencies else 0.0
    latency_p95 = p95(latencies) if latencies else 0.0

    run = {
        "api": api_name,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "passed": passed,
            "failed": failed,
            "error_rate": round(error_rate, 3),
            "latency_ms_avg": round(latency_avg, 1),
            "latency_ms_p95": round(latency_p95, 1),
        },
        "tests": results
    }
    return run