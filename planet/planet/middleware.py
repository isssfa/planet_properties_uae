# middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.conf import settings
from django.core.cache import cache
from google.cloud import translate_v2 as translate


def google_translate(text, target_lang, source_lang="en"):
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=target_lang, source_language=source_lang, format_="html")
    return result["translatedText"]

LANG_COOKIE = getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language")
SOURCE_LANG = getattr(settings, "SOURCE_LANGUAGE", "en")

def argos_translate(text, source, target):
    tr = None
    if source.startswith("en") and target.startswith("ar"):
        tr = getattr(settings, "ARGOS_EN_AR", None)
    elif source.startswith("ar") and target.startswith("en"):
        tr = getattr(settings, "ARGOS_AR_EN", None)
    if not tr:
        return text
    return tr.translate(text)

class AutoTranslateMiddleware(MiddlewareMixin):
    def process_request(self, req):
        lang = getattr(req, "session", {}).get(LANG_COOKIE) or req.COOKIES.get(LANG_COOKIE)
        if not lang:
            lang = translation.get_language_from_request(req, check_path=False)
        if lang:
            translation.activate(lang)
            req.LANGUAGE_CODE = translation.get_language()

    def process_response(self, req, resp):
        try:
            lang = getattr(req, "LANGUAGE_CODE", None) or translation.get_language()
            if hasattr(req, "session") and lang:
                req.session[LANG_COOKIE] = lang
            if lang:
                resp.set_cookie(LANG_COOKIE, lang, samesite="Lax")
            patch_vary_headers(resp, ["Accept-Language", "Cookie"])

            if "text/html" not in resp.get("Content-Type","") or resp.status_code != 200:
                return resp

            target = (lang or SOURCE_LANG)[:2]
            if target == SOURCE_LANG or target not in ("en", "ar"):
                return resp

            body = resp.content.decode(resp.charset or "utf-8")

            # Basic cache to avoid repeated work; include path+lang
            key = f"argos_mt:{target}:{hash(body)}:{req.get_full_path()}"
            translated = cache.get(key)
            if not translated:
                try:
                    translated = google_translate(body, target, SOURCE_LANG)
                except Exception as e:
                    print("Translation error:", e)
                    translated = body
                cache.set(key, translated, 3600)

            resp.content = translated.encode(resp.charset or "utf-8")
            resp["Content-Language"] = target
            return resp
        finally:
            translation.deactivate()
