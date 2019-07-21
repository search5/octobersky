import os
from os.path import abspath, join

SECRET_KEY = os.urandom(30)
SESSION_COOKIE_NAME = 'october_sky'
DEBUG = False
DEBUG_TB_INTERCEPT_REDIRECTS = False
SESSION_PROTECTION = 'strong'
INIT = True
IS_AWS = True

#if DEBUG:
#    SERVER_NAME = 'localhost'

APP_PATH = abspath(join(__file__, '..'))

SOCIAL_AUTH_LOGIN_URL = '/login'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/done/'
SOCIAL_AUTH_USER_MODEL = 'nanumlectures.models.User'
SOCIAL_AUTH_STORAGE = 'social_flask_sqlalchemy.models.FlaskStorage'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.kakao.KakaoOAuth2',
    'social_core.backends.username.UsernameAuth',
    'social_core.backends.naver.NaverOAuth2',
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'nanumlectures.common.user_login',
    'social_core.pipeline.user.create_user',
    'nanumlectures.common.user_create',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'nanumlectures.common.social_info',
    'social_core.pipeline.user.user_details'
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
  'locale': 'ko_KR',
  'fields': 'id, name, email'
}
SOCIAL_AUTH_FACEBOOK_API_VERSION = '2.10'

SOCIAL_AUTH_KAKAO_KEY = ''
SOCIAL_AUTH_KAKAO_SECRET = ''

SOCIAL_AUTH_NAVER_KEY = ''
SOCIAL_AUTH_NAVER_SECRET = ''
SOCIAL_AUTH_NAVER_EXTRA_DATA = ['nickname']

USER_FIELDS = ['username']

KAKAO_APPKEY = ''

S3_BUCKET_NAME = ''

AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

SES_HOST = ''
SES_ID = ""
SES_PASS = ""
