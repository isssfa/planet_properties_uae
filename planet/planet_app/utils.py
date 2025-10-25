import json
import random
import requests
import socket
from .models import *
from decimal import Decimal
from .currency import convert_amount, format_money, BASE
# utils.py
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
import requests
from django.conf import settings
from django.db import models, transaction
from django.apps import apps

# ----- Constants -----
BASE_CURRENCY = "AED"
SUPPORTED_CURRENCIES = {"AED", "USD", "EUR", "INR"}
CURRENCY_SYMBOLS = {"AED": "د.إ", "USD": "$", "EUR": "€", "INR": "₹"}

# ----- Inline model definition (optional) -----
# Prefer defining this in models.py with migrations. If already defined there, this reuses it.
DailyFxRates = next((m for m in apps.get_models(include_auto_created=False) if m.__name__ == "DailyFxRates"), None)

if DailyFxRates is None:
    class DailyFxRates(models.Model):
        as_of_date = models.DateField(unique=True)
        aed_to_usd = models.DecimalField(max_digits=18, decimal_places=8)
        aed_to_eur = models.DecimalField(max_digits=18, decimal_places=8)
        aed_to_inr = models.DecimalField(max_digits=18, decimal_places=8)
        fetched_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            app_label = "planet_app"  # TODO: set to your Django app label
            ordering = ["-as_of_date"]

        def __str__(self):
            return f"AED rates {self.as_of_date}"
# Model field choices and decimals match Django’s recommendations for money-like values. [web:57]

# ----- Provider fetch and normalization -----
def _normalize_to_aed(base_code: str, rates: dict) -> dict:
    """
    Convert provider rates (possibly base EUR) into AED->target for USD/EUR/INR.
    Requires that 'rates' include AED and targets. [web:27][web:59]
    """
    required = {"AED", "USD", "EUR", "INR"}
    missing = required - set(rates.keys())
    if missing:
        raise RuntimeError(f"Provider payload missing: {missing}")
    if base_code == BASE_CURRENCY:
        return {
            "USD": Decimal(str(rates["USD"])),
            "EUR": Decimal(str(rates["EUR"])),
            "INR": Decimal(str(rates["INR"])),
        }
    aed_per_base = Decimal(str(rates["AED"]))
    return {
        "USD": Decimal(str(rates["USD"])) / aed_per_base,
        "EUR": Decimal(str(rates["EUR"])) / aed_per_base,
        "INR": Decimal(str(rates["INR"])) / aed_per_base,
    }

def _fetch_from_provider() -> tuple[date, dict]:
    """
    Single API call to fetch latest FX and return (as_of_date, {'USD':..., 'EUR':..., 'INR':...}).
    Uses a Fixer-style endpoint; swap to any provider as needed. [web:27]
    """
    url = "https://data.fixer.io/api/latest"
    params = {
        "access_key": settings.FIXER_API_KEY,
        "symbols": "AED,USD,EUR,INR",
    }
    resp = requests.get(url, params=params, timeout=8)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"FX fetch failed: {data}")
    base = data.get("base", "EUR")
    normalized = _normalize_to_aed(base, data["rates"])
    as_of_str = data.get("date")
    as_of = date.fromisoformat(as_of_str) if as_of_str else date.today()
    return as_of, normalized  # normalization follows common patterns in exchange libs. [web:59]

# ----- Daily rate accessor (24h DB cache) -----
def get_daily_rates() -> dict:
    """
    Returns dict with AED base: {'AED': 1, 'USD': Decimal, 'EUR': Decimal, 'INR': Decimal}.
    Reads from DB; refreshes at most once per 24 hours using a transaction lock. [web:59]
    """
    latest = DailyFxRates.objects.first()
    now = datetime.utcnow()
    needs_refresh = True
    if latest:
        age = now - latest.fetched_at.replace(tzinfo=None)
        needs_refresh = age > timedelta(hours=24)

    if not latest or needs_refresh:
        with transaction.atomic():
            # Double-check freshness under lock to avoid races. [web:59]
            latest = DailyFxRates.objects.select_for_update().first()
            if not latest or (now - latest.fetched_at.replace(tzinfo=None)) > timedelta(hours=24):
                as_of, norm = _fetch_from_provider()
                latest, _ = DailyFxRates.objects.update_or_create(
                    as_of_date=as_of,
                    defaults={
                        "aed_to_usd": norm["USD"],
                        "aed_to_eur": norm["EUR"],
                        "aed_to_inr": norm["INR"],
                    },
                )

    return {
        "AED": Decimal("1"),
        "USD": latest.aed_to_usd,
        "EUR": latest.aed_to_eur,
        "INR": latest.aed_to_inr,
    }

# ----- Session currency helpers -----
def ensure_session_currency(request) -> str:
    """
    Ensure session['currency'] exists; default to AED if absent/invalid. Returns final code. [web:29]
    """
    code = request.session.get("currency")
    if not isinstance(code, str):
        request.session["currency"] = BASE_CURRENCY
        request.session.modified = True
        return BASE_CURRENCY
    code_up = code.upper()
    if code_up not in SUPPORTED_CURRENCIES:
        request.session["currency"] = BASE_CURRENCY
        request.session.modified = True
        return BASE_CURRENCY
    # Normalize to uppercase in session
    if code != code_up:
        request.session["currency"] = code_up
        request.session.modified = True
    return code_up

def set_session_currency(request, code: str) -> bool:
    """
    Set a supported currency in session; returns True if set, False if invalid. [web:29]
    """
    if not isinstance(code, str):
        return False
    c = code.upper()
    if c not in SUPPORTED_CURRENCIES:
        return False
    request.session["currency"] = c
    request.session.modified = True
    return True

# ----- Conversion/formatting -----
def convert_amount_from_aed(amount_aed, to_code: str, quantize="0.01") -> Decimal:
    """
    Convert an AED amount to target code using stored daily rates.
    Accepts only a 3-letter code string; call ensure_session_currency first for session defaulting. [web:59]
    """
    to = to_code.upper() if isinstance(to_code, str) else BASE_CURRENCY
    if to not in SUPPORTED_CURRENCIES:
        to = BASE_CURRENCY
    rates = get_daily_rates()
    rate = Decimal(str(rates.get(to, "1")))
    amt = Decimal(str(amount_aed)) * rate
    return amt.quantize(Decimal(quantize), rounding=ROUND_HALF_UP)

def format_money(amount: Decimal, code: str) -> str:
    sym = CURRENCY_SYMBOLS.get(code, code)
    return f"{sym} {amount:,.2f}"

def display_price_for_project(project, request) -> dict:
    """
    Read AED price from project.project_price, ensure session currency, convert/format safely. [web:29]
    """

    code = ensure_session_currency(request)
    try:
        price_aed = Decimal(str(project.project_price))
    except Exception:
        return {"price_raw": None, "price_display": None, "code": code}
    converted = convert_amount_from_aed(price_aed, code)
    return {
        "price_raw": converted,
        "price_display": format_money(converted, code),
        "code": code,
    }


def create_blocked_email(email):
    try:
        blocked = BlockedEmail.objects.filter(email=email)
        if not blocked:
            BlockedEmail.objects.create(email=email)
        return blocked
    except:
        return False


def check_email(email):
    blocked = BlockedEmail.objects.filter(email=email)
    if blocked:
        return False
    else:
        return True


def create_blocked_ip(ip):
    try:
        blocked = BlockedIP.objects.filter(ip=ip)
        if not blocked:
            BlockedIP.objects.create(ip=ip)
        return blocked
    except:
        return False


def check_ip(ip):
    blocked = BlockedIP.objects.filter(ip=ip)
    if blocked:
        return False
    else:
        return True


def create_blocked_word(word):
    try:
        blocked = BlockedWord.objects.filter(word=word.lower())
        if not blocked:
            BlockedWord.objects.create(word=word.lower())
        return blocked
    except:
        return False


def check_word(word):
    blocked = BlockedWord.objects.filter(word=word.lower())
    if blocked:
        return False
    else:
        return True


def create_blocked_name(name):
    try:
        blocked = BlockedName.objects.filter(name=name.lower())
        if not blocked:
            BlockedName.objects.create(name=name.lower())
        return blocked
    except:
        return False


def check_name(name):
    blocked = BlockedName.objects.filter(name=name.lower())
    if blocked:
        return False
    else:
        return True


def get_ip(request):
    response = requests.get("https://ipgeolocation.abstractapi.com/v1/?api_key=fee5bbcc75714df8859902d5816ea073")
    result = json.loads(response.content)
    return result['ip_address']


def get_random():
    return random.randint(1, 6)
