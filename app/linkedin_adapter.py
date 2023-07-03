from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount import app_settings

class MyAdapter(DefaultSocialAccountAdapter):

    def get_app(self, request, provider, config=None):
        # NOTE: Avoid loading models at top due to registry boot...
        from allauth.socialaccount.models import SocialApp

        config = config or app_settings.PROVIDERS.get(provider, {}).get("APP")
        if config:
            app = SocialApp(provider=provider)
            for field in ["client_id", "secret", "key", "certificate_key"]:
                setattr(app, field, config.get(field))
            app.key = app.key or 'unset'
            app.name=app.name or provider
            app.save()
        else:
            app = SocialApp.objects.get_current(provider, request)

        return app
