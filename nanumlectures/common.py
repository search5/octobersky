import os
import random
import string
from functools import wraps

import httplib2
import paginate
import yaml
from flask import flash, redirect, url_for, session
from flask_login import current_user
from google_auth_httplib2 import Request

from nanumlectures.database import db_session
from social_core.backends.google import GooglePlusAuth
from social_core.backends.utils import load_backends
from social_core.exceptions import AuthException
from social_core.pipeline.partial import partial
from sqlalchemy import func

from nanumlectures.models import GoogleToken


def common_context(authentication_backends, strategy, user=None, plus_id=None, **extra):
    """Common view context"""
    context = {
        'user': user,
        'available_backends': load_backends(authentication_backends),
        'associated': {}
    }

    if user and is_authenticated(user):
        context['associated'] = dict((association.provider, association)
                                     for association in associations(user, strategy))

    if plus_id:
        context['plus_id'] = plus_id
        context['plus_scope'] = ' '.join(GooglePlusAuth.DEFAULT_SCOPE)

    return dict(context, **extra)


def is_authenticated(user):
    if callable(user.is_authenticated):
        return user.is_authenticated()
    else:
        return user.is_authenticated


def associations(user, strategy):
    user_associations = strategy.storage.user.get_social_auth_for_user(user)
    if hasattr(user_associations, 'all'):
        user_associations = user_associations.all()
    return list(user_associations)


@partial
def user_login(strategy, backend, user, is_new=False, *args, **kwargs):
    req_data = strategy.request_data()

    if req_data.get('mode', 'login') == "login" and not user and not kwargs['social'] and is_new:
        flash("회원 가입을 하시거나 가입 후 소셜 로그인을 해주시기 바랍니다.")
        raise AuthException(backend)

    req_data = strategy.request_data()

    if req_data.get('mode', '') != "login":
        return False

    if (req_data.get('mode', '') == "login") and backend.name == "username" and not is_new:
        if not user.can_login(req_data['password']):
            raise AuthException(backend)

    user.last_login_date = func.now()


@partial
def user_create(strategy, backend, user, is_new=False, *args, **kwargs):
    req_data = strategy.request_data()

    is_backend_signup = (backend.name == "username")
    is_pipeline_mode = (req_data.get('mode', '') == "register")

    if not is_backend_signup:
        return False

    if is_backend_signup and (not is_pipeline_mode):
        return False

    if is_backend_signup and is_pipeline_mode and is_new:
        user.name = req_data['fullname']
        user.email = req_data['email']
        user.phone = req_data['phone']
        user.set_password(req_data['password'])
        user.last_login_date = func.now()

        db_session.add(user)


@partial
def social_info(strategy, backend, user, details, is_new=False, *args, **kwargs):
    if backend.name == "username":
        return

    if backend.name != "username":
        user.last_login_date = func.now()


def is_admin_role(func):
    @wraps(func)
    def chk_role(*args, **kwargs):
        if current_user.usertype == 'A':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('public.main'))
    return chk_role


def is_library_owner_role(func):
    @wraps(func)
    def chk_role(*args, **kwargs):
        if current_user.usertype == 'B':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('public.main'))
    return chk_role


def paginate_link_tag(item):
    """
    Create an A-HREF tag that points to another page usable in paginate.
    """
    item['attrs'] = {'class': 'page-link'}
    a_tag = paginate.Page.default_link_tag(item)

    if item['type'] == 'current_page':
        return paginate.make_html_tag('li', paginate.make_html_tag('a', a_tag), **{"class": "page-item active"})
    return paginate.make_html_tag("li", a_tag, **{"class": "page-item"})


def google_token(success_uri):
    def token_check_func(f):
        @wraps(f)
        def chk_role(*args, **kwargs):
            token_record = GoogleToken.query.first()
            if token_record:
                creds = yaml.load(token_record.token_content, yaml.Loader)

                # 토큰 정보을 갱신한다.
                if creds and creds.expired and creds.refresh_token:
                    http = httplib2.Http()
                    creds.refresh(Request(http))
                    token_record.token_content = yaml.dump(creds)

                    db_session.flush()

                return f(*args, **kwargs)
            else:
                session['success_uri'] = success_uri

                url_for_dict = {'_external': True, '_scheme': 'https'}
                if 'test' in os.environ:
                    del url_for_dict['_scheme']

                return redirect(url_for('admin.authorize', **url_for_dict))
        return chk_role
    return token_check_func


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
