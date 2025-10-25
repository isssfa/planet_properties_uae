from django.apps import AppConfig


class PlanetAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planet_app'


class CoreConfig(AppConfig):
    name = "planet_app"
    ready_called = False

    def ready(self):
        # Prevent double init under autoreload
        if CoreConfig.ready_called:
            return
        CoreConfig.ready_called = True

        import argostranslate.package as ap
        import argostranslate.translate as at

        # Ensure EN<->AR packages are installed
        ap.update_package_index()
        pkgs = ap.get_available_packages()
        for pair in [("en","ar"), ("ar","en")]:
            p = next((x for x in pkgs if x.from_code == pair[0] and x.to_code == pair[1]), None)
            if p:
                try:
                    ap.install_from_path(p.download())
                except Exception:
                    # Ignore if already installed or offline
                    pass

        # Build and cache translator objects globally
        from django.conf import settings
        installed = at.get_installed_languages()
        def find(code):
            return next((x for x in installed if x.code == code), None)
        en, ar = find("en"), find("ar")
        if en and ar:
            settings.ARGOS_EN_AR = en.get_translation(ar)
            settings.ARGOS_AR_EN = ar.get_translation(en)
