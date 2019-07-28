import paginate
from flask import render_template, jsonify, flash, redirect, url_for, request
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from social_flask_sqlalchemy.models import UserSocialAuth
from sqlalchemy import func, desc
from werkzeug.datastructures import MultiDict

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import Roundtable, Lecture, Library, VoteBooks, User, OTandParty


class LectureListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['lecture_name', 'session_time', 'lecture_title']:
            search_column = getattr(Lecture, search_option)

        if search_option == "roundtable_num" and search_word and not search_word.isdecimal():
            flash('개최회차는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.lecturer")
        if search_word:
            page_url = url_for("admin.lecturer", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(Lecture).outerjoin(Roundtable).outerjoin(Library)
        if search_word:
            if search_option == 'roundtable_num':
                records = records.filter(Roundtable.roundtable_num == search_word)
            elif search_option == 'library_name':
                records = records.filter(Library.library_name.ilike('%{}%'.format(search_word)))
            elif search_option == 'session_time':
                records = records.filter(search_column == int(search_word) - 1)
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(Lecture.roundtable_id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/lecturer.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class LectureFindView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        roundtable_id = request.args.get("roundtable_id", -1, type=int)
        library_id = request.args.get("library_id", -1, type=int)
        lecture_time = request.args.get("lecture_time", -1, type=int)

        if roundtable_id > -1 and lecture_time > -1:
            lecture_record = db_session.query(Lecture).filter(
                Lecture.roundtable_id == roundtable_id,
                Lecture.library_id == library_id,
                Lecture.session_time == lecture_time).first()
            if not lecture_record:
                return jsonify(success=True, msg='등록된 강연이 없습니다')

            return jsonify(success=False,
                           lecture_title=lecture_record.lecture_title)


class LectureRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        # 새로 입력할 회차 정보를 받아와서 넘겨준다
        # 단, 지난 회차에 강연자 정보를 등록할 일이 없다고 가정한다.
        main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

        # 만약 개최회차 등록되지 않았을 경우 개최회차 등록 화면으로 돌려보낸다.
        if not main_roundtable:
            flash('강연자를 등록하시려면 개최회차 등록부터 하셔야 합니다')
            return redirect(url_for('admin.roundtable_reg'))

        return render_template("admin/lecturer_reg.html", latest_roundtable=main_roundtable)

    def post(self):
        req_json = MultiDict(request.get_json())

        user_record = db_session.query(User).outerjoin(UserSocialAuth).filter(
            UserSocialAuth.uid == req_json.get("lectureID")).first()

        lecturer_obj = Lecture()
        lecturer_obj.roundtable_id = req_json.get('roundtable_id')
        lecturer_obj.library_id = req_json.get('library').get('id')
        lecturer_obj.session_time = req_json.get('lectureTime')
        lecturer_obj.lecture_title = req_json.get('lectureTitle')
        lecturer_obj.lecture_summary = req_json.get('lectureSummary')
        lecturer_obj.lecture_expected_audience = req_json.get('lectureExpectedAudience')
        lecturer_obj.lecture_user_id = (user_record and user_record.id) or None
        lecturer_obj.lecture_name = req_json.get('lectureName')
        lecturer_obj.lecture_belong = req_json.get('lectureBelong')
        lecturer_obj.lecture_hp = req_json.get('lectureHp')
        lecturer_obj.lecture_email = req_json.get('lectureEmail')
        lecturer_obj.lecture_public_yn = req_json.get('lectureUserYn', type=bool)

        db_session.add(lecturer_obj)

        return jsonify(success=True)


class LectureEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, lecturer):
        return render_template("admin/lecturer_edit.html", lecturer=lecturer)

    def post(self, lecturer):
        req_json = MultiDict(request.get_json())

        user_record = db_session.query(User).outerjoin(UserSocialAuth).filter(
            UserSocialAuth.uid == req_json.get("lectureID")).first()

        lecturer.library_id = req_json.get('library').get('id')
        lecturer.lecture_time = req_json.get('lectureTime')
        lecturer.lecture_title = req_json.get('lectureTitle')
        lecturer.lecture_summary = req_json.get('lectureSummary')
        lecturer.lecture_expected_audience = req_json.get('lectureExpectedAudience')
        lecturer.lecture_user_id = (user_record and user_record.id) or None
        lecturer.lecture_name = req_json.get('lectureName')
        lecturer.lecture_belong = req_json.get('lectureBelong')
        lecturer.lecture_hp = req_json.get('lectureHp')
        lecturer.lecture_email = req_json.get('lectureEmail')
        lecturer.lecture_public_yn = req_json.get('lecturePublicYn', type=bool)

        return jsonify(success=True)


class LectureDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, lecturer):
        vote_books = db_session.query(VoteBooks).filter(
            VoteBooks.roundtable_id == lecturer.roundtable_id,
            VoteBooks.lecture_user_id == lecturer.lecture_user_id).first()

        return render_template("admin/lecturer_view.html", lecturer=lecturer, vote_books=vote_books)

    def delete(self, lecturer):
        vote_books = db_session.query(VoteBooks).filter(
            VoteBooks.roundtable_id == lecturer.roundtable_id,
            VoteBooks.lecture_user_id == lecturer.lecture_user_id).first()

        if vote_books:
            db_session.delete(vote_books)

        db_session.query(OTandParty).filter(
            OTandParty.party_user_id == lecturer.lecture_user_id,
            OTandParty.roundtable_id == lecturer.roundtable_id).delete()

        db_session.delete(lecturer)

        return jsonify(success=True)
