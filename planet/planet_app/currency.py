# currency.py
import time
import requests
from decimal import Decimal, ROUND_HALF_UP
from django.core.cache import cache
from django.conf import settings

BASE = "AED"
SUPPORTED = ["AED", "USD", "EUR", "INR"]
CACHE_KEY = "fx_rates_aed"
CACHE_TTL = 600  # 10 minutes

def _fetch_rates_from_api():
    # Fixer-style API (base may require paid plan; if not available, fetch base=EUR and convert)
    api_key = settings.FIXER_API_KEY
    url = "https://data.fixer.io/api/latest"
    params = {"access_key": api_key, "symbols": ",".join(SUPPORTED)}
    resp = requests.get(url, params=params, timeout=8)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Rates fetch failed: {data}")
    base = data.get("base", "EUR")
    rates = data["rates"]  # dict of code->float relative to base
    # Normalize so rates are relative to AED (our BASE)
    if base == BASE:
        norm = {k: Decimal(str(v)) for k, v in rates.items()}
        norm[BASE] = Decimal("1")
        return norm
    # Ensure we have AED in the payload; if not, request symbols must include it
    if BASE not in rates:
        raise RuntimeError("Base AED not in provider rates; include it in symbols.")
    to_aed = Decimal(str(rates[BASE]))  # AED per base unit
    # For any currency C, rate_AED->C = rates[C] / rates[AED]
    norm = {}
    for code in SUPPORTED:
        if code == BASE:
            norm[code] = Decimal("1")
        else:
            norm[code] = Decimal(str(rates[code])) / to_aed
    return norm

def get_rates():
    rates = cache.get(CACHE_KEY)
    if rates:
        return rates
    rates = _fetch_rates_from_api()
    cache.set(CACHE_KEY, rates, CACHE_TTL)
    return rates

def convert_amount(amount_aed, to_code, quantize="0.01"):
    """
    Convert Decimal/float amount from AED to to_code using cached live rates.
    Returns Decimal quantized to given step (default 2 decimals).
    """
    to = (to_code or BASE).upper()
    if to not in SUPPORTED:
        to = BASE
    rates = get_rates()
    rate = rates.get(to, Decimal("1"))
    amt = Decimal(str(amount_aed)) * rate
    return amt.quantize(Decimal(quantize), rounding=ROUND_HALF_UP)

def format_money(amount, code):
    symbols = {"AED": "د.إ", "USD": "$", "EUR": "€", "INR": "₹"}
    sym = symbols.get(code, code)
    # Simple symbol-prefix formatting
    return f"{sym}{amount:,.2f}"
