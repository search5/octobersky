import paginate
from flask import request, url_for, render_template, jsonify, flash
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import Books, Roundtable


class BooksListView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['books_title']:
            search_column = getattr(Books, search_option)

        if search_option == "roundtable_num" and search_word and not search_word.isdecimal():
            flash('개최회차는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.books")
        if search_word:
            page_url = url_for("admin.books", search_option=search_option, search_word=search_word)

        page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(Books).join(Roundtable)
        if search_word:
            if search_option == 'roundtable_num':
                records = records.filter(Roundtable.roundtable_num == search_word)
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(Books.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/books.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class BooksRegView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self):
        return render_template("admin/books_reg.html")

    def post(self):
        req_json = request.get_json()

        # 도서 관리 추가
        books_obj = Books()
        books_obj.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == req_json.get('roundtable_num')).first()
        books_obj.books_title = req_json.get('booksTitle')
        books_obj.books_link = req_json.get('booksLink')
        books_obj.books_isbn = req_json.get('booksISBN')
        books_obj.books_date = req_json.get('booksDate')
        books_obj.books_company = req_json.get('booksCompany')
        books_obj.books_body = req_json.get('booksBody')
        books_obj.books_bookshop = req_json.get('shopLink')

        db_session.add(books_obj)

        return jsonify(success=True)


class BooksEditView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self, book):
        return render_template("admin/books_edit.html", book=book)

    def post(self, book):
        req_json = request.get_json()

        # 도서 관리
        book.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == req_json.get('roundtable_num')).first()
        book.books_title = req_json.get('booksTitle')
        book.books_link = req_json.get('booksLink')
        book.books_isbn = req_json.get('booksISBN')
        book.books_date = req_json.get('booksDate')
        book.books_company = req_json.get('booksCompany')
        book.books_body = req_json.get('booksBody')
        book.books_bookshop = req_json.get('shopLink')

        return jsonify(success=True)


class BooksDetailView(MethodView):
    decorators = [login_required, is_admin_role]

    def get(self, book):
        return render_template("admin/books_view.html", book=book)

    def delete(self, book):
        db_session.delete(book)

        return jsonify(success=True)
