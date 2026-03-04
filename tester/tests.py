import re

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def _fail(name, details):
    return {"name": name, "ok": False, "latency_ms": None, "details": details}

def test_200_latest_eur_usd(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "EUR", "to": "USD"})
    ok = (err is None and resp is not None and resp.status_code == 200)
    return {"name": "GET /latest?from=EUR&to=USD returns 200", "ok": ok, "latency_ms": ms,
            "details": err or f"status={resp.status_code if resp else 'no_resp'}"}

def test_content_type_json(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "EUR", "to": "USD"})
    if err or resp is None:
        return _fail("Content-Type contains application/json", err or "no response")
    ct = resp.headers.get("Content-Type", "")
    return {"name": "Content-Type contains application/json", "ok": ("application/json" in ct), "latency_ms": ms, "details": ct}

def test_json_parse(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "EUR", "to": "USD"})
    if err or resp is None:
        return _fail("Body is valid JSON", err or "no response")
    try:
        _ = resp.json()
        return {"name": "Body is valid JSON", "ok": True, "latency_ms": ms, "details": ""}
    except Exception as e:
        return {"name": "Body is valid JSON", "ok": False, "latency_ms": ms, "details": str(e)}

def test_required_fields(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "EUR", "to": "USD"})
    if err or resp is None or resp.status_code != 200:
        return _fail("JSON has required fields (amount/base/date/rates)", err or f"status={resp.status_code if resp else 'no_resp'}")
    data = resp.json()
    required = ["amount", "base", "date", "rates"]
    ok = all(k in data for k in required)
    return {"name": "JSON has required fields (amount/base/date/rates)", "ok": ok, "latency_ms": ms, "details": str(list(data.keys()))}

def test_types_and_date_format(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "EUR", "to": "USD", "amount": "10"})
    if err or resp is None or resp.status_code != 200:
        return _fail("Types OK + date format YYYY-MM-DD", err or f"status={resp.status_code if resp else 'no_resp'}")
    data = resp.json()

    ok_amount = isinstance(data.get("amount"), (int, float))
    ok_base = isinstance(data.get("base"), str)
    ok_date = isinstance(data.get("date"), str) and bool(ISO_DATE_RE.match(data["date"]))
    ok_rates = isinstance(data.get("rates"), dict)

    ok = ok_amount and ok_base and ok_date and ok_rates
    return {"name": "Types OK + date format YYYY-MM-DD", "ok": ok, "latency_ms": ms,
            "details": f"amount={type(data.get('amount'))}, base={type(data.get('base'))}, date={data.get('date')}, rates={type(data.get('rates'))}"}

def test_rate_usd_present_and_numeric(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "EUR", "to": "USD"})
    if err or resp is None or resp.status_code != 200:
        return _fail("rates.USD exists and is numeric", err or f"status={resp.status_code if resp else 'no_resp'}")
    data = resp.json()
    usd = data.get("rates", {}).get("USD")
    ok = isinstance(usd, (int, float))
    return {"name": "rates.USD exists and is numeric", "ok": ok, "latency_ms": ms, "details": f"USD={usd}"}

def test_invalid_currency_returns_4xx(client, base_url):
    resp, ms, err = client.get(f"{base_url}/latest", params={"from": "NOPE", "to": "USD"})
    if err or resp is None:
        return _fail("Invalid currency (from=NOPE) returns 4xx", err or "no response")
    ok = 400 <= resp.status_code < 500
    return {"name": "Invalid currency (from=NOPE) returns 4xx", "ok": ok, "latency_ms": ms, "details": f"status={resp.status_code}"}