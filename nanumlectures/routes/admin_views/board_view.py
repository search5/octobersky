import paginate
from flask import request, url_for, render_template, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc, func

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import BoardModel


class BoardListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option:
            search_column = getattr(BoardModel, search_option)

        page_url = url_for("admin.board")
        if search_word:
            page_url = url_for("admin.board", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(BoardModel)
        if search_word:
            records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(BoardModel.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/preparatory_committee/list.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class BoardRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        return render_template("admin/preparatory_committee/reg.html")

    def post(self):
        req_json = request.get_json()

        board_obj = BoardModel()
        board_obj.title = req_json.get('title')
        board_obj.content = req_json.get('content')
        board_obj.wdate = func.now()
        board_obj.mdate = func.now()
        board_obj.user_id = current_user.id
        board_obj.hit = 0

        db_session.add(board_obj)

        return jsonify(success=True)


class BoardEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, board):
        return render_template("admin/preparatory_committee/edit.html", board=board)

    def post(self, board):
        req_json = request.get_json()

        board.title = req_json.get('title')
        board.content = req_json.get('content')
        board.mdate = func.now()

        return jsonify(success=True)


class BoardDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, board):
        board.hit += 1

        return render_template("admin/preparatory_committee/view.html", board=board)

    def delete(self, board):
        db_session.delete(board)

        return jsonify(success=True)
