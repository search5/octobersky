import traceback

import flask_login
from dateutil.utils import today

from nanumlectures.common import common_context
from nanumlectures.lib.format_util import date_format
from nanumlectures.lib.public_context import line_break, is_ie_browser
from nanumlectures.lib.upload import s3_object_url
from nanumlectures.lib.url_util import (LibraryConverter, UserConverter,
                                        UserModelConverter, FAQConverter,
                                        LectureConverter, SessionHostConverter,
                                        NewsConverter, BooksConverter,
                                        RoundtableConverter, PhotoConverter,
                                        DesignDataConverter, GoodsDonationConverter, BoardConverter)
from nanumlectures.routes import public, admin
from flask import Flask, render_template, g, redirect, url_for, flash, request
from flask_login import current_user
from markupsafe import Markup
from nanumlectures.settings import KAKAO_APPKEY
from social_core.exceptions import AuthException
from social_flask.routes import social_auth
from nanumlectures.database import db_session
from social_flask.template_filters import backends
from social_flask.utils import load_strategy
from social_flask_sqlalchemy.models import init_social

from nanumlectures.models import User

app = Flask(__name__, static_url_path='/static')
app.config.from_object('nanumlectures.settings')

app.url_map.converters['library'] = LibraryConverter
app.url_map.converters['user'] = UserConverter
app.url_map.converters['user_model'] = UserModelConverter
app.url_map.converters['roundtable'] = RoundtableConverter
app.url_map.converters['faq'] = FAQConverter
app.url_map.converters['lecturer'] = LectureConverter
app.url_map.converters['host'] = SessionHostConverter
app.url_map.converters['news'] = NewsConverter
app.url_map.converters['book'] = BooksConverter
app.url_map.converters['photo'] = PhotoConverter
app.url_map.converters['design'] = DesignDataConverter
app.url_map.converters['donation'] = GoodsDonationConverter
app.url_map.converters['board'] = BoardConverter

app.register_blueprint(social_auth)
app.register_blueprint(public.page)
app.register_blueprint(admin.page)
init_social(app, db_session)

# flask_login.set_login_view('main', public.page)
login_manager = flask_login.LoginManager()
login_manager.login_view = 'public.login_page'
login_manager.login_message = '로그인하셔야 이용 가능합니다.'
login_manager.init_app(app)


@app.route('/.well-known/acme-challenge/<challenge_id>')
def acme_challenge(challenge_id):
    """Let's Encrypt SSL Cerificate"""
    return "upjjvewCxU0m1ksFHunVR4qBbk69b0sgMlJsoq4g_5Q.5mCvJf1FQxq2aT-Y6Xi68lmL4yH4hwMOqWFoNZhJD_4"


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/public'):
        return render_template("public/404.html")
    elif request.path.startswith('/admin'):
        return render_template("admin/404.html")
    else:
        return render_template("public/404.html")


@app.errorhandler(500)
def interval_server(e: ValueError):
    if isinstance(e, AuthException):
        flash("로그인에 실패했습니다. Username 또는 Password를 확인하여 주십시오")
        return redirect(url_for('public.login_page'))

    if request.path.startswith('/public'):
        return render_template("500.html", error=str(e))
    elif request.path.startswith('/admin'):
        return render_template("admin/500.html", error=str(e))


@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception is None:
        db_session.commit()
    else:
        db_session.rollback()

    db_session.remove()


@login_manager.user_loader
def load_user(userid):
    try:
        return db_session.query(User).filter(User.username == userid).first()
    except (TypeError, ValueError):
        pass


@app.before_request
def global_user():
    # evaluate proxy value
    g.user = current_user._get_current_object()


# Make current user available on templates
@app.context_processor
def inject_user():
    try:
        return {'user': g.user}
    except AttributeError:
        return {'user': None}


@app.context_processor
def load_common_context():
    return common_context(
        app.config['SOCIAL_AUTH_AUTHENTICATION_BACKENDS'],
        load_strategy(),
        getattr(g, 'user', None),
        app.config.get('SOCIAL_AUTH_GOOGLE_PLUS_KEY')
    )


app.context_processor(backends)


@app.context_processor
def context_util():
    return {
        "date_format": date_format,
        "zip": zip,
        "tuple": tuple,
        "kakao_key": KAKAO_APPKEY,
        "line_break": line_break,
        "s3_object_url": s3_object_url,
        "is_ie_browser": is_ie_browser,
        "today": today().strftime("%Y%m%d%H%m")
    }


@app.template_filter("category_name")
def category_name(value):
    return {1: "보도자료", 2: "뉴스기사"}[value]


@app.template_filter("design_file_name")
def design_file_name(value):
    return tuple(value)[0]


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
