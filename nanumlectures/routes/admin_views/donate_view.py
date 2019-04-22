from flask import request, render_template, jsonify, render_template_string
from flask.views import MethodView
from flask_login import login_required
from markupsafe import Markup

from nanumlectures.common import is_admin_role
from nanumlectures.database import db_session
from nanumlectures.models import PageTemplate


class DonateEditView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self):
        page_record = db_session.query(PageTemplate).filter(
            PageTemplate.page_name == 'public/boost.html').first()

        return render_template("admin/donate_edit.html",
                               page_content=Markup(page_record.page_content))

    def post(self):
        req_json = request.get_json()

        page_record = db_session.query(PageTemplate).filter(
            PageTemplate.page_name == 'public/boost.html').first()
        page_record.page_content = req_json.get('page_content')

        return jsonify(success=True)


class DonatePreviewView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self):
        page_record = db_session.query(PageTemplate).filter(
            PageTemplate.page_name == 'public/boost.html').first()

        return render_template(
            'public/boost.html', donate_body=Markup(
                render_template_string(page_record.page_content)))
