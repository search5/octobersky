from datetime import date

import paginate
from flask import request, url_for, render_template, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import FAQ


class FaqListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['classify', 'subject']:
            search_column = getattr(FAQ, search_option)

        page_url = url_for("admin.faq")
        if search_word:
            page_url = url_for("admin.faq", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(FAQ)
        if search_word:
            records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(FAQ.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/faq.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class FaqRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        return render_template("admin/faq_reg.html")

    def post(self):
        req_json = request.get_json()

        faq_obj = FAQ()
        faq_obj.classify = req_json.get('faqClassify')
        faq_obj.subject = req_json.get('faqSubject')
        faq_obj.body = req_json.get('faqBody')
        faq_obj.writer_id = current_user.id

        db_session.add(faq_obj)

        return jsonify(success=True)


class FaqEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, faq):
        return render_template("admin/faq_edit.html",faq=faq)

    def post(self, faq):
        req_json = request.get_json()

        faq.classify = req_json.get('faqClassify')
        faq.subject = req_json.get('faqSubject')
        faq.body = req_json.get('faqBody')

        return jsonify(success=True)


class FaqDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, faq):
        return render_template("admin/faq_view.html",faq=faq)

    def delete(self, faq):
        db_session.delete(faq)

        return jsonify(success=True)
