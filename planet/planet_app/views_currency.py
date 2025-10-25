from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST

@require_POST
def set_currency(request):
    code = (request.POST.get("currency") or "").upper()
    SUPPORTED_CURRENCIES = {"AED", "USD", "EUR", "INR"}
    if code not in SUPPORTED_CURRENCIES:
        if request.is_ajax():
            return JsonResponse({"ok": False, "error": "Unsupported currency"}, status=400)
        # fallback: redirect to home
        return HttpResponseRedirect("/")
    request.session["currency"] = code
    request.session.modified = True
    # AJAX: return JSON, otherwise redirect
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "currency": code})
    # Non-AJAX: Redirect to referrer or home
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
