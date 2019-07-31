import requests
from django.conf import settings
from django.dispatch import receiver
from allauth.account.signals import user_signed_up, user_logged_out
from allauth.socialaccount.signals import social_account_updated

from allauth_janus.helper import janus_sync_user_properties


@receiver(social_account_updated)
def social_account_updated(sender, request, sociallogin, **kwargs):

    if sociallogin.account.provider == "janus":
        janus_sync_user_properties(request, sociallogin)


@receiver(user_signed_up)
def user_signed_up(sender, request, user, **kwargs):

    sociallogin = kwargs.get('sociallogin', None)

    if sociallogin and sociallogin.account.provider == "janus":
        janus_sync_user_properties(request, sociallogin)


@receiver(user_logged_out)
def user_logged_out(sender, request, user, **kwargs):
    """
    send a logout command to the sso janus instance to ensure no token or session is valid
    if the user return for authorisation
    """

    from allauth.socialaccount.models import SocialToken
    token = SocialToken.objects.filter(account__user=user, account__provider='janus').first()

    remote_logout = bool(settings.get('ALLAUTH_REMOTE_LOGOUT', False))

    if remote_logout and token:
        url = settings.ALLAUTH_JANUS_URL + '/o/logout/'
        try:
            response = requests.get(
                url,
                params={'access_token': token}
            )
            if response.content == "OK":
                pass
        except Exception as e:
            pass
