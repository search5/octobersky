from datetime import date

import paginate
from flask import request, url_for, render_template, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import News


class NewsListView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['press_date', 'category', 'news_title', 'news_press']:
            search_column = getattr(News, search_option)

        page_url = url_for("admin.news")
        if search_word:
            page_url = url_for("admin.news", search_option=search_option, search_word=search_word)

        page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(News)
        if search_word:
            records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(News.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/news.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class NewsRegView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self):
        return render_template("admin/news_reg.html")

    def post(self):
        req_json = request.get_json()

        news_obj = News()
        news_obj.category = req_json.get('pressCategory')
        news_obj.press_date = req_json.get('pressDate')
        news_obj.news_title = req_json.get('newsTitle')
        news_obj.news_press = req_json.get('newsPress')
        news_obj.news_link = req_json.get('newsLink')
        news_obj.news_body = req_json.get('newsBody')
        news_obj.writer_id = current_user.id

        db_session.add(news_obj)

        return jsonify(success=True)


class NewsEditView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self, news):
        return render_template("admin/news_edit.html", news=news)

    def post(self, news):
        req_json = request.get_json()

        # Summer Note Body / 날짜 임시로 설정
        news.category = req_json.get('pressCategory')
        news.press_date = req_json.get('pressDate')
        news.news_title = req_json.get('newsTitle')
        news.news_press = req_json.get('newsPress')
        news.news_link = req_json.get('newsLink')
        news.news_body = req_json.get('newsBody')

        return jsonify(success=True)


class NewsDetailView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self, news):
        return render_template("admin/news_view.html", news=news)

    def delete(self, news):
        db_session.delete(news)

        return jsonify(success=True)
