import paginate
import requests
from bs4 import BeautifulSoup
from flask import request, url_for, render_template, jsonify, flash
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import Books, Roundtable
from nanumlectures.settings import SOCIAL_AUTH_NAVER_KEY, SOCIAL_AUTH_NAVER_SECRET


class BooksListView(MethodView):
    decorators = [is_admin_role, login_required]

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
            page_url = str(page_url) + "&page=$page"
        else:
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
    decorators = [is_admin_role, login_required]

    def get(self):
        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/books_reg.html", roundtable=roundtable)

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
    decorators = [is_admin_role, login_required]

    def get(self, book):
        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/books_edit.html", book=book, roundtable=roundtable)

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
    decorators = [is_admin_role, login_required]

    def get(self, book):
        return render_template("admin/books_view.html", book=book)

    def delete(self, book):
        db_session.delete(book)

        return jsonify(success=True)


def date_simple_format(text):
    return "{}-{}-{}".format(text[0:4], text[4:6], text[6:])


class BookFindNaverAPI(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):

        headers = {
            'X-Naver-Client-Id': SOCIAL_AUTH_NAVER_KEY,
            'X-Naver-Client-Secret': SOCIAL_AUTH_NAVER_SECRET
        }

        r = requests.get('https://openapi.naver.com/v1/search/book_adv.xml?d_isbn=' + request.args.get('isbn'),
                         headers=headers)
        book_info = BeautifulSoup(r.content.decode("utf-8"), "lxml")

        link_aladin_req = requests.get(
            "https://openapi.naver.com/v1/search/webkr.json?query={}".format("알라딘 " + request.args.get('isbn')),
            headers=headers)
        link_yes24_req = requests.get(
            "https://openapi.naver.com/v1/search/webkr.json?query={}".format("예스24 " + request.args.get('isbn')),
            headers=headers)
        link_ypbooks_req = requests.get(
            "https://openapi.naver.com/v1/search/webkr.json?query={}".format("영풍문고 " + request.args.get('isbn')),
            headers=headers)

        aladin_link = tuple(filter(lambda x: 'www.aladin.co.kr' in x["link"], link_aladin_req.json()["items"]))
        yes24_link = tuple(filter(lambda x: 'www.yes24.com' in x["link"], link_yes24_req.json()["items"]))
        ypbook_link = tuple(filter(lambda x: 'www.ypbooks.co.kr' in x["link"], link_ypbooks_req.json()["items"]))

        return jsonify(title=book_info.find("item").title.text,
            image=book_info.find("item").image.text,
            author=book_info.find("item").author.text,
            pubdate=date_simple_format(book_info.find("item").pubdate.text),
            description=book_info.find("item").description.text,
            publisher=book_info.find("item").publisher.text,
            store_link=dict(
                aladin=aladin_link and aladin_link[0]["link"],
                yes24=yes24_link and yes24_link[0]["link"],
                ypbook=ypbook_link and ypbook_link[0]["link"])
        )
