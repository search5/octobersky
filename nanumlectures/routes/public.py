from flask import (render_template, Blueprint, redirect, url_for, request,
                   jsonify, send_file, render_template_string)
from flask_login import login_required, logout_user, current_user
from markupsafe import Markup
from social_flask_sqlalchemy.models import UserSocialAuth
from werkzeug.datastructures import MultiDict

from nanumlectures.database import db_session
from nanumlectures.lib.public_context import short2long_name, library2dict, user_lectureAndHostExist, donate2record, \
    modifed_allow_date, batch_fill
from nanumlectures.models import (User, FAQ, Lecture,
                                  SessionHost, News, Books, PhotoAlbum,
                                  DesignData, PageTemplate, Roundtable, Library,
                                  RoundtableAndLibrary)
from sqlalchemy import desc, func
import paginate
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from nanumlectures.common import paginate_link_tag

from io import BytesIO
from nanumlectures.lib.upload import download_blob


page = Blueprint('public', __name__, static_folder='../static/public')


@page.route("/")
def main():
    # 최근건 몇 개를 표시하는 것은 항목이 모자를 경우 빈 항목으로 채우고 템플릿에서 처리하게 한다.

    # 최근 언론보도 3건
    latest_news = list(db_session.query(News).order_by(desc(News.id)).limit(3))
    if len(latest_news) < 3:
        latest_news = latest_news + [None for _ in range(3 - len(latest_news))]

    # 최근 사진첩 3건
    latest_photo = list(db_session.query(PhotoAlbum).order_by(desc(PhotoAlbum.id)).limit(3))
    if len(latest_photo) < 3:
        latest_photo = latest_photo + [None for _ in range(3 - len(latest_photo))]

    return render_template("public/index.html", latest_news=latest_news, latest_photo=latest_photo)


@page.route("/about")
def about():
    return render_template("public/about.html")


@page.route("/manifesto")
def manifesto():
    return render_template("public/manifesto.html")


@page.route("/news")
def news():
    """
    언론 홍보 목록
    """
    current_page = request.args.get("page", 1, type=int)

    page_url = url_for("public.news")
    page_url = str(page_url) + "?page=$page"

    items_per_page = 7

    records = db_session.query(News).order_by(desc(News.id))
    total_cnt = records.count()

    paginator = paginate.Page(records, current_page, page_url=page_url,
                              items_per_page=items_per_page,
                              wrapper_class=SqlalchemyOrmWrapper)

    return render_template("public/news.html", paginator=paginator,
                           paginate_link_tag=paginate_link_tag,
                           page_url=page_url, items_per_page=items_per_page,
                           total_cnt=total_cnt, page=current_page)


@page.route("/news/<news:news>")
def news_view(news):
    """
    언론 홍보 조회
    """

    return render_template("public/news_view.html", news=news)


@page.route("/login")
def login_page():
    return render_template("public/login.html")


@page.route("/register")
def user_register():
    return render_template("public/user/register.html")


@page.route("/myinfo")
@login_required
def myinfo():
    user = db_session.query(User.username, User.name, User.email, User.phone,
                            UserSocialAuth.provider, User.last_login_date, User.usertype, UserSocialAuth, User).join(
        UserSocialAuth, User.id == UserSocialAuth.user_id).filter(
        User.id == current_user.id).first()

    return render_template("public/user/myinfo.html", user=user)


# 회원 정보 수정
@page.route("/myinfo/edit", methods=["POST"])
@login_required
def myinfo_edit():
    req_json = request.get_json()

    user_obj = db_session.query(User).filter(User.id == current_user.id).first()
    if req_json.get('new_password'):
        if user_obj.can_login(req_json.get('current_password', '')):
            user_obj.set_password(req_json.get('password'))

    user_obj.name = req_json.get('name')
    user_obj.email = req_json.get('email')
    user_obj.phone = req_json.get('phone')

    return jsonify(success=True)


@page.route('/donation/delete', methods=['POST'])
@login_required
def delete_donation():
    req_data = MultiDict(request.get_json())

    cancel_id = req_data.get('cancel_id')

    record = None
    if req_data.get('cancel_type') == 'lecture':
        record = db_session.query(Lecture).filter(Lecture.id == cancel_id).first()
    elif req_data.get('cancel_type') == 'host':
        record = db_session.query(SessionHost).filter(SessionHost.id == cancel_id).first()

    if not record:
        return jsonify(success=False, message='무엇을 삭제하려 했습니까?')

    print(record)
    db_session.delete(record)

    return jsonify(success=True)


@page.route('/donation/<donation_type>/<donation_id>')
@login_required
def donation_info(donation_type, donation_id):
    query_cls = Lecture
    if donation_type == 'host':
        query_cls = SessionHost

    record = db_session.query(query_cls).filter(query_cls.id == donation_id).first()
    record_dict = donate2record(record, donation_type)

    library = db_session.query(Library, RoundtableAndLibrary).join(
        RoundtableAndLibrary).filter(Library.id == record.library_id).filter(
        RoundtableAndLibrary.roundtable_id == record.roundtable_id).first()

    req_lecture_info = db_session.query(Lecture).filter(Lecture.library == library[0],
                                                        Lecture.roundtable_id == record.roundtable_id)

    def session_time_filter(entry):
        if entry.lecture_user_id != current_user.id:
            return entry.session_time

        # 관리자가 수동으로 추가하는 경우는 강연자 ID가 비어있을 수 있다.
        if not entry.lecture_user_id and entry.lecture_name:
            return entry.session_time

    joined_session_time = tuple(filter(lambda x: x, map(session_time_filter, req_lecture_info)))

    all_session_time = list(range(1, library[1].round_num + 1))
    for item in joined_session_time:
        all_session_time.remove(item)

    return jsonify(success=True, record=record_dict, available_session_time=all_session_time)


@page.route('/donation/<donation_type>/<donation_id>', methods=['POST'])
@login_required
def donation_info_edit(donation_type, donation_id):
    req_data = MultiDict(request.get_json())

    query_cls = Lecture
    if donation_type == 'host':
        query_cls = SessionHost

    record = db_session.query(query_cls).filter(query_cls.id == donation_id).first()
    record.lecture_title = req_data.get('title', '')
    record.lecture_summary = req_data.get('description', '')
    record.lecture_public_yn = req_data.get('public_yn', '', type=bool)
    record.session_time = req_data.get('session_time', -1, type=int)
    record.lecture_expected_audience = req_data.get('expectedaudience', '')

    return jsonify(success=True, message='오늘도 찾아주셔서 감사합니다.')


@page.route("/privacy")
def privacy():
    return render_template("public/user/privacy.html")


# FAQ 불러오기
@page.route("/faq")
def faq():
    records = db_session.query(FAQ).order_by(desc(FAQ.id))

    return render_template("public/faq.html", faqs=records)


@page.route('/together_library')
def together_library():
    # 최근 회차 정보 가져오기
    latest_round_num = db_session.query(Roundtable.id, func.max(
        Roundtable.roundtable_num)).group_by(
        Roundtable.id).first()

    # 강연이 열리는 지역 가져오기
    area_opened_library = db_session.query(func.distinct(Library.area)).join(
        RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == latest_round_num[0])

    opened_area = [entry[0] for entry in area_opened_library]

    area = request.args.get('area', None) or opened_area[0]

    opened_library = db_session.query(Library, RoundtableAndLibrary).join(
        RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == latest_round_num[0])
    opened_library = opened_library.filter(Library.area == area)

    joined_user = False
    if current_user.is_authenticated:
        joined_user = user_lectureAndHostExist(latest_round_num)

    return render_template('public/together_library.html',
                           opened_library=opened_library,
                           show_roundtable_num=latest_round_num[0],
                           area=opened_area,
                           joined_user=joined_user)


@page.app_context_processor
def public_context_processor():
    return {
        "library_filter": lambda lecture, round_num: tuple(filter(lambda x: x.roundtable_id == round_num, lecture)),
        "batch_fill": batch_fill,
        "library_short2long": short2long_name,
        'modifed_allow_date': modifed_allow_date
    }


@page.app_template_filter('social_name')
@login_required
def social_name(name):
    return {"google-oauth2": '구글 로그인', 'facebook': '페이스북', 'kakao': '카카오', 'naver': '네이버'}[name]


@page.route('/library_info')
def library_info():
    library_id = request.args.get('library_id', 0, type=int)
    session_time = request.args.get('session_time', 0, type=int)
    roundtable_id = request.args.get('roundtable_id', type=int)

    if library_id and session_time:
        library = db_session.query(Library, RoundtableAndLibrary).join(
            RoundtableAndLibrary).filter(Library.id == library_id).filter(
            RoundtableAndLibrary.roundtable_id == roundtable_id).first()

        req_lecture_info = db_session.query(Lecture).filter(Lecture.library == library[0],
                                                            Lecture.roundtable_id == roundtable_id)
        joined_session_time = tuple(map(lambda x: x.session_time, req_lecture_info))

        all_session_time = list(range(1, library[1].round_num + 1))
        for item in joined_session_time:
            all_session_time.remove(item)

        return jsonify(success=True, library=library2dict(library[0]), available_session_time=all_session_time)
    else:
        return jsonify(success=False)


@page.route('/reg_lecture', methods=['POST'])
@login_required
def reg_lecture():
    req_json = MultiDict(request.get_json())

    already_library = db_session.query(Lecture).filter(Lecture.roundtable_id == req_json.get('roundtable_num'),
                                                       Lecture.library_id==req_json.get('library_id'),
                                                       Lecture.session_time==req_json.get('session_time')).first()

    if already_library:
        return jsonify(success=False, msg='신청하신 도서관의 강연 시간에 다른 분이 신청하셨습니다')

    lecturer_obj = Lecture()
    lecturer_obj.roundtable_id = req_json.get('roundtable_num')
    lecturer_obj.library_id = req_json.get('library_id')
    lecturer_obj.session_time = req_json.get('session_time')
    lecturer_obj.lecture_title = req_json.get('title')
    lecturer_obj.lecture_summary = req_json.get('description')
    lecturer_obj.lecture_expected_audience = req_json.get('expectedaudience')
    lecturer_obj.lecture_user_id = current_user.id
    lecturer_obj.lecture_name = current_user.name
    lecturer_obj.lecture_belong = req_json.get('organization')
    lecturer_obj.lecture_hp = current_user.phone or req_json.get('phone')
    lecturer_obj.lecture_email = current_user.email or req_json.get('email')
    lecturer_obj.lecture_public_yn = req_json.get('public_yn', type=bool)

    db_session.add(lecturer_obj)

    user_record = db_session.query(User).filter(User.id == current_user.id).first()

    if not current_user.phone and req_json.get('phone'):
        user_record.phone = req_json.get('phone')

    if not current_user.email and req_json.get('email'):
        user_record.email = req_json.get('email')

    return jsonify(success=True)


@page.route('/reg_host', methods=['POST'])
@login_required
def reg_host():
    req_json = MultiDict(request.get_json())

    already_host = db_session.query(SessionHost).filter(SessionHost.roundtable_id == req_json.get('roundtable_num'),
                                                        SessionHost.library_id==req_json.get('library_id'),
                                                        SessionHost.session_time==req_json.get('session_time'))

    if already_host.count() == 2:
        return jsonify(success=False, msg='신청하신 도서관은 진행자 모집이 완료되었습니다.')

    session_host_obj = SessionHost()
    session_host_obj.roundtable_id = req_json.get('roundtable_num')
    session_host_obj.library_id = req_json.get('library_id')
    session_host_obj.session_time = 1 if already_host.count() == 0 else 2
    session_host_obj.host_user_id = current_user.id
    session_host_obj.host_name = current_user.name
    session_host_obj.host_belong = req_json.get('organization')
    session_host_obj.host_hp = current_user.phone or req_json.get('phone')
    session_host_obj.host_email = current_user.email or req_json.get('email')
    session_host_obj.host_use_yn = True
    db_session.add(session_host_obj)

    user_record = db_session.query(User).filter(User.id == current_user.id).first()

    if not current_user.phone and req_json.get('phone'):
        user_record.phone = req_json.get('phone')

    if not current_user.email and req_json.get('email'):
        user_record.email = req_json.get('email')

    return jsonify(success=True)


@page.route('/boost')
def boost():
    donate_body = db_session.query(PageTemplate).filter(
        PageTemplate.page_name == 'public/boost.html').first()

    return render_template('public/boost.html', donate_body=Markup(
        render_template_string(donate_body.page_content)))


# 사진 가져오기
@page.route('/archive/photo')
def archive_photo():
    current_page = request.args.get("page", 1, type=int)

    page_url = url_for("public.archive_photo")
    page_url = str(page_url) + "?page=$page"

    items_per_page = 10

    records = db_session.query(PhotoAlbum).order_by(desc(PhotoAlbum.id))
    total_cnt = records.count()

    paginator = paginate.Page(records, current_page, page_url=page_url,
                              items_per_page=items_per_page,
                              wrapper_class=SqlalchemyOrmWrapper)

    return render_template("public/photo.html", paginator=paginator,
                           paginate_link_tag=paginate_link_tag,
                           page_url=page_url, items_per_page=items_per_page,
                           total_cnt=total_cnt, page=current_page)


# 책 정보 가져오기
@page.route('/archive/books')
def archive_books():
    current_page = request.args.get("page", 1, type=int)

    page_url = url_for("public.archive_books")
    page_url = str(page_url) + "?page=$page"

    items_per_page = 10

    records = db_session.query(Books).order_by(desc(Books.id))
    total_cnt = records.count()

    paginator = paginate.Page(records, current_page, page_url=page_url,
                              items_per_page=items_per_page,
                              wrapper_class=SqlalchemyOrmWrapper)

    return render_template("public/books.html", paginator=paginator,
                           paginate_link_tag=paginate_link_tag,
                           page_url=page_url, items_per_page=items_per_page,
                           total_cnt=total_cnt, page=current_page)


# 디자인 파일 가져오기
@page.route('/archive/design')
def archive_design():
    current_page = request.args.get("page", 1, type=int)

    page_url = url_for("public.archive_design")
    page_url = str(page_url) + "?page=$page"

    items_per_page = 10

    records = db_session.query(DesignData).order_by(desc(DesignData.id))
    total_cnt = records.count()

    paginator = paginate.Page(records, current_page, page_url=page_url,
                              items_per_page=items_per_page,
                              wrapper_class=SqlalchemyOrmWrapper)

    return render_template("public/design.html", paginator=paginator,
                           paginate_link_tag=paginate_link_tag,
                           page_url=page_url, items_per_page=items_per_page,
                           total_cnt=total_cnt, page=current_page)


# 디자인 파일 가져오기
@page.route('/archive/design/download')
def archive_design_download():
    design = request.args.get('design', None)  # use default value replace 'None'
    filename = request.args.get('filename', None)

    record = db_session.query(DesignData).filter(DesignData.id == design)
    design = record.first()
    download_file = BytesIO()
    download_blob(design.design_files[filename], download_file)
    download_file.seek(0)

    return send_file(
        download_file,
        as_attachment=True,
        attachment_filename=filename)


@page.route('/done/')
@login_required
def done():
    return redirect(url_for('public.main'))


@page.route('/logout/')
@login_required
def logout():
    """Logout view"""
    logout_user()
    return redirect('/')
