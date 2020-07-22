from django.http import HttpResponseRedirect
from django.urls import reverse

import google.auth as google_auth
from requests_oauthlib import OAuth2Session
from djangae.contrib import googleauth as auth


STATE_SESSION_KEY = 'oauth-state'
_DEFAULT_OAUTH_SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"

GOOGLE_USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

_DEFAULT_WHITELISTED_SCOPES = _DEFAULT_OAUTH_SCOPES[:]


def login(request):
    """
        This view should be set as your login_url for using OAuth
        authentication. It will trigger the main oauth flow.
    """
    original_url = f"{request.scheme}://{request.META['HTTP_HOST']}{reverse('googleauth_oauth2callback')}"

    next_url = request.GET.get('next')
    if next_url:
        request.session[auth.REDIRECT_FIELD_NAME] = next_url

    credentials, project = google_auth.default()
    google = OAuth2Session(credentials.client_id, scope=_DEFAULT_WHITELISTED_SCOPES, redirect_uri=original_url)
    authorization_url, state = google.authorization_url(
        AUTHORIZATION_BASE_URL,
        access_type="offline",
        prompt="select_account"
    )
    request.session[STATE_SESSION_KEY] = state

    return HttpResponseRedirect(authorization_url)


def oauth2callback(request):

    original_url = f"{request.scheme}://{request.META['HTTP_HOST']}{reverse('googleauth_oauth2callback')}"

    credentials, project = google_auth.default()
    google =  OAuth2Session(
        credentials.client_id,
        state=request.session[STATE_SESSION_KEY],
        redirect_uri=original_url
    )

    token = google.fetch_token(
        TOKEN_URL,
        client_secret=credentials.client_secret,
        authorization_response=request.build_absolute_uri()
    )
    next_url = request.session[auth.REDIRECT_FIELD_NAME]
    if google.authorized and next_url:
        r = google.get(GOOGLE_USER_INFO)
        raw_user = r.json()
        # credentials are valid, we should authenticate the user
        user = auth.authenticate(request, username=raw_user.get('id'), email=raw_user.get('email'), token=token)
        auth.login(request, user)
        return HttpResponseRedirect(next_url)

    return HttpResponseRedirect(reverse("googleauth_oauth2login"))
