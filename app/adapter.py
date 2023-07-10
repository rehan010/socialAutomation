from urllib import response

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount,SocialToken


# from app.models import User


class CustomAccountAdapter(DefaultSocialAccountAdapter):
    def get_app(self, request, provider,config=None):
        # NOTE: Avoid loading models at top due to registry boot...
        from allauth.socialaccount.models import SocialApp
        # 1 added line here
        from allauth.socialaccount import app_settings

        # config = app_settings.PROVIDERS.get(provider, {}).get('APP')
        # print(config)
        # if config:
        #     app = SocialApp(provider=provider)
        #     for field in ['client_id', 'secret', 'key']:
        #         setattr(app, field, config.get(field))
        #
        #     # 3 added lines here
        #     app.key = app.key or "unset"
        #     app.name = app.name or provider
        #     app.save()

        # else:
        app = SocialApp.objects.get_current(provider, request)
        return app