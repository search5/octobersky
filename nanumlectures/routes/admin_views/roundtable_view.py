import paginate
from flask import render_template, jsonify, request, url_for, flash
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc, func

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import Roundtable, RoundtableAndLibrary, Library, Lecture, SessionHost


class RoundtableListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option:
            search_column = getattr(Roundtable, search_option)

        if search_word and not search_word.isdecimal():
            flash('검색어는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.roundtable_list")
        if search_word:
            page_url = url_for("admin.roundtable_list", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(Roundtable)
        if search_word:
            records = records.filter(search_column == search_word)
        records = records.order_by(desc(Roundtable.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/roundtable_list.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class RoundtableRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        return render_template("admin/roundtable_reg.html")

    def post(self):
        req_json = request.get_json()

        obj = Roundtable()
        obj.roundtable_num = req_json.get('roundtableNum')
        obj.roundtable_year = req_json.get('roundtableYear')
        obj.roundtable_date = req_json.get('roundtableDate')
        obj.staff = req_json.get('staff')

        for item in req_json.get('library_list'):
            lib_info = RoundtableAndLibrary(round_num=item.get('session_time'), library_type=item.get('library_type'))
            lib_info.library = db_session.query(Library).filter(Library.id == item.get('library').get('id')).first()
            obj.library.append(lib_info)

        db_session.add(obj)

        return jsonify(success=True)


class RoundtableEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, round):
        return render_template("admin/roundtable_edit.html", round=round)

    def post(self, round):
        req_json = request.get_json()

        round.roundtable_num = req_json.get('roundtableNum')
        round.roundtable_year = req_json.get('roundtableYear')
        round.roundtable_date = req_json.get('roundtableDate')
        round.staff = req_json.get('staff')

        worked_lib = []

        for entry in round.library:
            put_library = tuple(filter(lambda sub_entry: entry.library_id == sub_entry.get('library').get('id'), req_json.get('library_list')))
            if len(put_library) > 0:
                worked_lib.append(entry.library_id)
                entry.round_num = put_library[0]['session_time']
                entry.library_type = put_library[0]['library_type']
            else:
                # 사용자가 보낸 도서관을 목록에서 찾지 못하면 삭제 대상으로 결정한다.
                db_session.delete(entry)

        for item in req_json.get('library_list'):
            if item.get('library').get('id') in worked_lib:
                continue

            lib_info = RoundtableAndLibrary(round_num=item.get('session_time'), library_type=item.get('library_type'))
            lib_info.library = db_session.query(Library).filter(Library.id == item.get('library').get('id')).first()
            round.library.append(lib_info)

        return jsonify(success=True)


class RoundtableDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, round):
        # 뷰 페이지에서 참여 도서관을 검색할 수 있도록 추가 기능 개선
        opened_library = [{
            "library": {
                'library_name': entry.library.library_name,
                'library_addr': entry.library.library_addr
            },
            "round_num": entry.round_num
        } for entry in round.library]

        return render_template("admin/roundtable_view.html", round=round, opened_library=opened_library)

    def delete(self, round):
        # 참여 도서관 정보 삭제
        for entry in round.library:
            db_session.delete(entry)

        db_session.query(Lecture).filter(Lecture.roundtable_id == round.id).delete()
        db_session.query(SessionHost).filter(SessionHost.roundtable_id == round.id).delete()

        db_session.delete(round)

        return jsonify(success=True)


class RoundtableActiveView(MethodView):
    decorators = [is_admin_role, login_required]

    def post(self):
        req_json = request.get_json()

        # roundtable_id만 제외하고 나머지 레코드는 활성화 여부를 비활성화로 바꾼다.
        db_session.query(Roundtable).filter(Roundtable.id != req_json.get('roundtable_id')).update({"is_active": False})

        record = db_session.query(Roundtable).filter(Roundtable.id == req_json.get('roundtable_id')).first()
        record.is_active = req_json.get('checked')

        # 만약 설정 상태를 요청받은 애가 False인 경우 가장 늦게 입력된 회차 레코드의 활성화 여부를 True로 설정한다.
        if not req_json.get('checked'):
            max_latest_id = db_session.query(func.max(Roundtable.id)).first()
            db_session.query(Roundtable).filter(Roundtable.id == max_latest_id).update({"is_active": True})

        return jsonify(success=True)
