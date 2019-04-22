from functools import wraps

import paginate
from flask_login import current_user
from nanumlectures.database import db_session
from social_core.backends.google import GooglePlusAuth
from social_core.backends.utils import load_backends
from social_core.exceptions import AuthException
from social_core.pipeline.partial import partial
from sqlalchemy import func


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

    if backend.name != 'username':
        return
    else:
        if strategy.request_data()['mode'] != "login":
            return

    if not user:
        raise AuthException(backend)

    # 로그인한 유저가 소셜 유저인지 일반 유저인지 확인한다.
    if user.social_user_yn == 'Y':
        raise AuthException(backend)

    password = strategy.request_data()['password']

    if not user.can_login(password):
        raise AuthException(backend)

    user.last_login_date = func.now()


@partial
def user_create(strategy, backend, user, is_new=False, *args, **kwargs):

    if backend.name != 'username':
        return
    else:
        if strategy.request_data()['mode'] != "register":
            return

    if not user:
        raise AuthException(backend)

    password = strategy.request_data()['password']

    user.name = strategy.request_data()['fullname']
    user.email = strategy.request_data()['email']
    user.phone = strategy.request_data()['phone']
    user.set_password(password)

    db_session.add(user)


@partial
def social_info(strategy, backend, user, details, is_new=False, *args, **kwargs):
    if backend.name == "username":
        return

    user.name = details['fullname']
    user.last_login_date = func.now()
    if is_new:
        user.created_date = func.now()
        user.usertype = 'C'
        user.social_user_yn = 'Y'

    db_session.add(user)


def is_admin_role(func):
    @wraps(func)
    def chk_role(*args, **kwargs):
        if current_user.usertype == 'A':
            return func(*args, **kwargs)
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
