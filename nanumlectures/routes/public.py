import base64
import json
import mimetypes
import os

import requests
from flask import (render_template, Blueprint, redirect, url_for, request,
                   jsonify, send_file, render_template_string, abort, make_response)
from flask_login import login_required, logout_user, current_user
from markupsafe import Markup
from social_flask_sqlalchemy.models import UserSocialAuth
from werkzeug.datastructures import MultiDict

from nanumlectures.database import db_session
from nanumlectures.lib.mail_lib import SESMail
from nanumlectures.lib.public_context import short2long_name, library2dict, user_lectureAndHostExist, donate2record, \
    modified_allow_date, statstics_summary, latest_is_donation, shortcut_summary
from nanumlectures.models import (User, FAQ, Lecture,
                                  SessionHost, News, Books, PhotoAlbum,
                                  DesignData, PageTemplate, Roundtable, Library,
                                  RoundtableAndLibrary, VoteBooks, DonationGoods, FindPasswordToken, SlideCarousel,
                                  OTandParty)
from sqlalchemy import desc, func, asc, literal_column
import paginate
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from nanumlectures.common import paginate_link_tag

from io import BytesIO
from nanumlectures.lib.upload import download_blob, s3_object_url
import uuid, datetime
import hashlib

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

    # 개최일을 카운트다운 하기 위한 추가 작업(메인으로 하고 있는 개최회차 정보를 가져옴)
    main_roundtable_record = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()
    round_open_date = main_roundtable_record.roundtable_date.strftime("%Y/%m/%d")

    # 메인 이미지 내려주기
    slide_carousel = SlideCarousel.query.order_by(asc(SlideCarousel.id))

    # 도서관 수 반환
    open_library_cnt = db_session.query(func.count(RoundtableAndLibrary.roundtable_id)).filter(
        RoundtableAndLibrary.roundtable_id == main_roundtable_record.id).first()

    return render_template(
        "public/index.html",
        latest_news=latest_news,
        latest_photo=latest_photo,
        round_open_date=round_open_date,
        slide_carousel=slide_carousel,
        open_library_cnt=open_library_cnt[0])


@page.route("/about")
def about():
    return render_template("public/about.html")


@page.route("/manifesto")
def manifesto():
    return render_template("public/manifesto.html")


@page.route("/news")
def news():
    """언론 홍보 목록"""
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
    background_image = base64.b64encode(page.open_resource('../static/public/img/login-bg3.jpg').read())
    return render_template("public/login.html", background_image=background_image.decode("latin1"))


@page.route("/register")
def user_register():
    return render_template("public/user/register.html")


@page.route("/donation_goods")
@login_required
def donation_goods():
    # 메인 회차 정보 가져오기
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    return render_template("public/donation_goods.html", show_roundtable_num=main_roundtable.id)


@page.route("/donation_goods", methods=['POST'])
def goods_donation():
    req_json = request.get_json()

    record = DonationGoods()
    record.roundtable_id = req_json.get('roundtable_num')
    record.lecture_user_id = current_user.id
    record.donation_type = req_json.get('donation_type')
    record.donation_description = req_json.get('donation_description')
    record.donation_transport = req_json.get('donation_transport_type')

    db_session.add(record)

    return jsonify(success=True, msg='신청되었습니다')


@page.route("/donation_goods/<id>", methods=['POST'])
def goods_donation_mod(id):
    req_json = request.get_json()

    record = DonationGoods.query.filter(DonationGoods.id == id).first()
    if record:
        record.donation_type = req_json.get('donation_type')
        record.donation_description = req_json.get('donation_description')
        record.donation_transport = req_json.get('donation_transport_type')

    return jsonify(success=True, msg='수정되었습니다')


@page.route("/myinfo")
@login_required
def myinfo():
    user = db_session.query(User.username, User.name, User.email, User.phone,
                            UserSocialAuth.provider, User.last_login_date, User.usertype, UserSocialAuth, User).join(
        UserSocialAuth, User.id == UserSocialAuth.user_id).filter(
        User.id == current_user.id, UserSocialAuth.provider == 'username').first()

    # 아래 정보를 추가하는건 도서문화재단 씨앗의 추가 요청사항이 있어서임

    # 가장 최근의 회차 정보를 가져온다.
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 강연자가 최근 회차로 신청한 강연 ID를 가져온다.
    lecture_rec = Lecture.query.filter(Lecture.roundtable_id == main_roundtable.id,
                                       Lecture.lecture_user_id == current_user.id).order_by(desc(Lecture.id)).first()

    # 추천도서 정보가 있는지 확인한다.
    is_vote_btn = False

    is_vote_record = False
    if lecture_rec:
        vote_record = VoteBooks.query.filter(VoteBooks.roundtable_id == main_roundtable.id,
                                             VoteBooks.lecture_id == lecture_rec.id).first()
        if vote_record:
            is_vote_record = True

    # Case 1) 강연 신청를 아예 안한 경우
    # Case 2) 강연 신청은 했지만 추천도서 정보를 입력 안한 경우
    # Case 3) 강연 신청도 하고 추천도서 정보도 입력한 경우

    if lecture_rec and not is_vote_record:
        # Case 3
        is_vote_btn = True

    # 해당 유저가 도서관 사서인지 확인한다. 확인 방법은 이메일로 한다(전화번호는 휴대폰 번호로 입력 안할수도 있기 때문)
    is_librarian = False
    librarian_office = None

    library_record = Library.query.filter(Library.manager_email == user[2]).first()
    if library_record:
        librarian_office = library_record

        # 물론 이 때 이미 해당 유저가 사서로 등록되어 있으면 경고창을 다시 보여주면 안된다
        # (하하... 도대체 누구 좋으라고 이 코드를 만드는가..)
        is_librarian = True
        if library_record.manager_id == current_user.id:
            is_librarian = False

    return render_template("public/user/myinfo.html", user=user, is_vote_btn=is_vote_btn,
                           is_librarian=is_librarian, librarian_office=librarian_office)


@page.route("/myinfo/edit", methods=["POST"])
@login_required
def myinfo_edit():
    """회원 정보 수정"""
    req_json = request.get_json()

    user_obj = db_session.query(User).filter(User.id == current_user.id).first()
    if req_json.get('new_password'):
        if user_obj.can_login(req_json.get('current_password', '')):
            user_obj.set_password(req_json.get('password'))

    user_obj.name = req_json.get('name')

    # 사서에 해당할 수 있는데 이때 이메일 주소가 바뀌면 사서로 생각하지 않는다.
    library_record = Library.query.filter(Library.manager_id == user_obj.id).first()

    if library_record and (user_obj.email != req_json.get('email')):
        user_obj.usertype = 'C'
        library_record.manager_id = None

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

    if req_data.get('cancel_type') == 'lecture':
        vote_books = db_session.query(VoteBooks).filter(
            VoteBooks.roundtable_id == record.roundtable_id,
            VoteBooks.lecture_user_id == record.lecture_user_id).first()

        if vote_books:
            db_session.delete(vote_books)
    db_session.delete(record)

    # 현재 운영중인 회차 정보를 가져와서 참석 여부 레코드를 삭제한다.
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()
    db_session.query(OTandParty).filter(
        OTandParty.party_user_id == current_user.id,
        OTandParty.roundtable_id == main_roundtable.id).delete()

    return jsonify(success=True)


@page.route('/donation_goods/delete', methods=['POST'])
@login_required
def delete_donation_goods():
    req_json = request.get_json()
    cancel_id = req_json.get('cancel_id')

    record = DonationGoods.query.filter(DonationGoods.id == cancel_id).first()
    if record:
        db_session.delete(record)

    return jsonify(success=True, msg='삭제되었습니다')


@page.route('/donation/<donation_type>/<donation_id>')
@login_required
def donation_info(donation_type, donation_id):
    query_cls = Lecture
    vote_books = None
    if donation_type == 'host':
        query_cls = SessionHost
    else:
        vote_books = db_session.query(VoteBooks).filter(
            VoteBooks.roundtable_id == query_cls.roundtable_id,
            VoteBooks.lecture_user_id == query_cls.lecture_user_id).first()
        if vote_books:
            vote_books = dict(vote_books)

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

    return jsonify(success=True, record=record_dict, available_session_time=all_session_time, vote_books=vote_books or [])


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
    record.lecture_belong = req_data.get('organization')

    return jsonify(success=True, message='오늘도 찾아주셔서 감사합니다.')


@page.route("/privacy")
def privacy():
    return render_template("public/user/privacy.html")


# FAQ 불러오기
@page.route("/faq")
def faq():
    records = db_session.query(FAQ).order_by(desc(FAQ.id))

    return render_template("public/faq.html", faqs=records)


@page.route("/lecture_library_map")
def lecture_library_map():
    # 최근 회차 정보 가져오기
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 강연이 열리는 지역 가져오기
    area_opened_library = db_session.query(func.distinct(Library.area)).join(
        RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == main_roundtable.id,
        RoundtableAndLibrary.library_type == '일반')

    req_area = request.args.get('area', None) or "all"
    if type(req_area) == str:
        req_area = {"name": req_area}

    opened_area = [{"name": entry[0]} for entry in area_opened_library]
    opened_area.append({"name": '특별한 도서관'})

    round_library_items = db_session.query(Library, RoundtableAndLibrary).join(
        RoundtableAndLibrary).filter(RoundtableAndLibrary.roundtable_id == main_roundtable.id)

    round_library_items2 = db_session.query(Library, RoundtableAndLibrary).join(
        RoundtableAndLibrary).filter(RoundtableAndLibrary.roundtable_id == main_roundtable.id)

    if req_area["name"] != "all":
        # 10회차 한정 코드가 될지도 모르지만 특별한 도서관(SF/장애인/다문화)만 따로 필터링해서 보여주도록 한다
        # 동작 조건은 특별한 도서관 일때만, 다만 특별한 도서관이 아닌 경우는 지역별 도서관 정보를 가져온다.
        # 이 기능은 이민아 선생님 요청사항입니다(의견을 많이 주셔서 특별히 반영해드립니다)
        if req_area == '특별한 도서관':
            round_library_items = round_library_items.filter(RoundtableAndLibrary.library_type.in_(['SF', '장애인', '다문화']))
        else:
            round_library_items = round_library_items.filter(Library.area == req_area["name"])
            round_library_items = round_library_items.filter(RoundtableAndLibrary.library_type == '일반')

    # 신청 가능한 통계 잡아주기 위해 사용
    statics_area_cnt = {}
    statics_library = round_library_items2.filter(RoundtableAndLibrary.library_type == '일반')
    statstics_summary(statics_area_cnt, statics_library)

    statics_library = round_library_items2.filter(RoundtableAndLibrary.library_type.in_(['SF', '장애인', '다문화']))
    statstics_summary(statics_area_cnt, statics_library, '특별한 도서관')

    # 지역별로 열리는 도서관 수 뽑아와야 함..(이건 생각보다 좀 걸리네..)
    opened_library_cnt = db_session.query(Library.id).join(RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == main_roundtable.id)
    gen_q = dict(db_session.query(Library.area, func.count(Library.area)).filter(
        Library.id.in_(opened_library_cnt.filter(RoundtableAndLibrary.library_type == '일반'))).group_by(Library.area))
    gen_q['특별한 도서관'] = len(tuple(statics_library))

    for idx, item in enumerate(opened_area):
        stat_area_item = statics_area_cnt.get(item["name"])
        if stat_area_item is None:
            opened_area[idx]["statics"] = "()"
            continue
        stat_lecture = stat_area_item['total_round_num'] - stat_area_item['total_lecture']
        stat_host = stat_area_item['total_round_num'] - stat_area_item['total_host']
        opened_area[idx]["statics"] = Markup('<span style="font-size: 12px;"> {}개 ({}명, {}명)</span>'.format(gen_q[item["name"]], stat_lecture, stat_host))

    library_list = []

    for library, round_and_library in round_library_items:
        library_list.append({
            "library_name": library.library_name,
            "id": library.id,
            "lat": library.lat,
            "long": library.long,
            "addr": library.library_addr,
            "tel": library.library_tel,
            "homepage": library.library_homepage
        })

    return render_template(
        "public/lecture_library_map.html",
        library=library_list,
        area=opened_area)


@page.route('/lecture_application_donate')
def lecture_application_donate():
    # 최근 회차 정보 가져오기
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 강연이 열리는 지역 가져오기
    area_opened_library = db_session.query(func.distinct(Library.area)).join(
        RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == main_roundtable.id,
        RoundtableAndLibrary.library_type == '일반')

    opened_area = [{"name": entry[0]} for entry in area_opened_library]
    opened_area.append({"name": '특별한 도서관'})

    first_area_name = opened_area[0] if len(opened_area) > 0 else ''

    area = request.args.get('area', None) or first_area_name
    if type(area) == str:
        area = {"name": area}

    opened_library = db_session.query(Library, RoundtableAndLibrary).join(
        RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == main_roundtable.id)

    statics_area_cnt = {}
    statics_library = opened_library.filter(RoundtableAndLibrary.library_type == '일반')
    statstics_summary(statics_area_cnt, statics_library)

    statics_library = opened_library.filter(RoundtableAndLibrary.library_type.in_(['SF', '장애인', '다문화']))
    statstics_summary(statics_area_cnt, statics_library, '특별한 도서관')

    # 지역별로 열리는 도서관 수 뽑아와야 함..(이건 생각보다 좀 걸리네..)
    opened_library_cnt = db_session.query(Library.id).join(RoundtableAndLibrary).filter(
        RoundtableAndLibrary.roundtable_id == main_roundtable.id)
    gen_q = dict(db_session.query(Library.area, func.count(Library.area)).filter(
        Library.id.in_(opened_library_cnt.filter(RoundtableAndLibrary.library_type == '일반'))).group_by(Library.area))
    gen_q['특별한 도서관'] = len(tuple(statics_library))

    for idx, item in enumerate(opened_area):
        stat_area_item = statics_area_cnt.get(item["name"])
        if stat_area_item is None:
            opened_area[idx]["statics"] = "()"
            continue
        stat_lecture = stat_area_item['total_round_num'] - stat_area_item['total_lecture']
        stat_host = stat_area_item['total_round_num'] - stat_area_item['total_host']
        opened_area[idx]["statics"] = Markup('<span style="font-size: 12px;"> {}개 ({}명, {}명)</span>'.format(gen_q[item["name"]], stat_lecture, stat_host))

    # 10회차 한정 코드가 될지도 모르지만 특별한 도서관(SF/장애인/다문화)만 따로 필터링해서 보여주도록 한다
    # 동작 조건은 특별한 도서관 일때만, 다만 특별한 도서관이 아닌 경우는 지역별 도서관 정보를 가져온다.
    # 이 기능은 이민아 선생님 요청사항입니다(의견을 많이 주셔서 특별히 반영해드립니다)
    if area == '특별한 도서관':
        opened_library = opened_library.filter(RoundtableAndLibrary.library_type.in_(['SF', '장애인', '다문화']))
    else:
        opened_library = opened_library.filter(Library.area == area["name"])
        opened_library = opened_library.filter(RoundtableAndLibrary.library_type == '일반')

    joined_user = False
    if current_user.is_authenticated:
        joined_user = user_lectureAndHostExist(main_roundtable)

    return render_template('public/lecture_application_donate.html',
                           opened_library=opened_library,
                           show_roundtable_num=main_roundtable.id,
                           area=opened_area,
                           joined_user=joined_user,
                           current_user=current_user)


def library_sessions(library, show_roundtable_num, round_num):
    round_only_filter = lambda lecture, roundtable_num: list(filter(lambda x: x.roundtable_id == roundtable_num, lecture))

    round_only_lecture = round_only_filter(library.lecture, show_roundtable_num)
    round_only_host = round_only_filter(library.host, show_roundtable_num)

    # 도서관별 세션 횟수 별로 비어있는 항목을 추가한다.
    round_only_host.extend([None] * (round_num - len(round_only_host)))

    new_round_only_lecture = []

    for item in range(round_num):
        session_round = list(filter(lambda x: x and x.session_time == (item + 1), round_only_lecture))

        try:
            new_round_only_lecture.append(session_round[0])
        except:
            new_round_only_lecture.append(None)

    round_only_lecture = new_round_only_lecture

    library_assoc_host = []

    # 강연은 시간별로 체크해서 비어있는지 아닌지 판단해야 한다.
    for lecture, host in zip(round_only_lecture, round_only_host):
        library_assoc_host.append((lecture, host))

    return library_assoc_host


@page.route("/vote_books")
def vote_books():
    current_page = request.args.get("page", 1, type=int)

    page_url = url_for("public.vote_books")
    page_url = str(page_url) + "?page=$page"

    items_per_page = 7

    records = db_session.query(VoteBooks).order_by(desc(VoteBooks.id))
    total_cnt = records.count()

    paginator = paginate.Page(records, current_page, page_url=page_url,
                              items_per_page=items_per_page,
                              wrapper_class=SqlalchemyOrmWrapper)

    return render_template("public/vote_book.html", paginator=paginator,
                           paginate_link_tag=paginate_link_tag,
                           page_url=page_url, items_per_page=items_per_page,
                           total_cnt=total_cnt, page=current_page)


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

    lecture_obj = Lecture()
    lecture_obj.roundtable_id = req_json.get('roundtable_num')
    lecture_obj.library_id = req_json.get('library_id')
    lecture_obj.session_time = req_json.get('session_time')
    lecture_obj.lecture_title = req_json.get('title')
    lecture_obj.lecture_summary = req_json.get('description')
    lecture_obj.lecture_expected_audience = req_json.get('expectedaudience')
    lecture_obj.lecture_user_id = current_user.id
    lecture_obj.lecture_name = current_user.name
    lecture_obj.lecture_belong = req_json.get('organization')
    lecture_obj.lecture_hp = current_user.phone or req_json.get('phone')
    lecture_obj.lecture_email = current_user.email or req_json.get('email')
    lecture_obj.lecture_public_yn = req_json.get('public_yn', type=bool)

    db_session.add(lecture_obj)
    db_session.flush()

    user_record = db_session.query(User).filter(User.id == current_user.id).first()

    if not current_user.phone and req_json.get('phone'):
        user_record.phone = req_json.get('phone')

    if not current_user.email and req_json.get('email'):
        user_record.email = req_json.get('email')

    return jsonify(success=True, lecture_id=lecture_obj.id)


@page.route("/reg_votebook", methods=["POST"])
@login_required
def reg_votebook():
    req_json = request.get_json()

    # 추천 도서 정보 기록
    vote_book = VoteBooks()
    vote_book.roundtable_id = req_json.get('roundtable_num')
    vote_book.lecture_id = req_json.get('lecture_id')
    vote_book.lecture_user_id = current_user.id
    vote_book.book_info = {
        'book1': req_json.get('book1'),
        'book1_desc': req_json.get('book1_desc'),
        'book2': req_json.get('book2'),
        'book3': req_json.get('book3'),
        'etc': req_json.get('etc')
    }
    vote_books.enter_path = req_json.get("enter_path")

    db_session.add(vote_book)
    db_session.flush()

    return jsonify(success=True)


@page.route("/add_votebook", methods=["POST"])
@login_required
def add_votebook():
    req_json = request.get_json()

    # 가장 최근의 회차 정보를 가져온다.
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 강연자가 최근 회차로 신청한 강연 ID를 가져온다.
    lecture_rec = Lecture.query.filter(Lecture.roundtable_id == main_roundtable.id,
                                       Lecture.lecture_user_id == current_user.id).order_by(desc(Lecture.id)).first()

    # 추천 도서 정보 기록
    vote_book = VoteBooks()
    vote_book.roundtable_id = main_roundtable.id
    vote_book.lecture_id = lecture_rec.id
    vote_book.lecture_user_id = current_user.id
    vote_book.book_info = {
        'book1': req_json.get('book1'),
        'book1_desc': req_json.get('book1_desc'),
        'book2': req_json.get('book2'),
        'book3': req_json.get('book3'),
        'etc': req_json.get('etc')
    }
    vote_books.enter_path = req_json.get("enter_path")

    db_session.add(vote_book)
    db_session.flush()

    return jsonify(success=True)


@page.route('/mod_votebook', methods=['POST'])
@login_required
def mod_votebook():
    req_json = request.get_json()

    # 추천 도서 정보 기록
    vote_book = VoteBooks.query.filter(VoteBooks.id == req_json.get('vote_id')).first()
    vote_book.book_info = {
        'book1': req_json.get('book1'),
        'book1_desc': req_json.get('book1_desc'),
        'book2': req_json.get('book2'),
        'book3': req_json.get('book3'),
        'etc': req_json.get('etc')
    }

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


@page.route('/find_password')
def find_password():
    # 비밀번호 찾기
    return render_template("public/find_password.html")


@page.route('/find_match_password', methods=['POST'])
def find_match_password():
    req_json = request.get_json()
    find_username = req_json.get('find_username')
    find_email = req_json.get('find_email')
    find_name = req_json.get('find_name')
    find_count = db_session.query(User).filter(User.username == find_username,
                                               User.email == find_email,
                                               User.name == find_name).count()
    if find_count == 1:
        # 아이디, 이메일, 이름 동일한 경우
        # 유효기간 : 10분
        uuid_string = uuid.uuid4().__str__()
        expire_date = datetime.datetime.now()
        expire_date_timedelta = datetime.timedelta(seconds=600)
        expire_date += expire_date_timedelta
        find_object = db_session.query(User).filter(
            User.username == find_username,
            User.email == find_email,
            User.name == find_name)

        # 해당되는 uuid Table Insert
        find_password_obj = FindPasswordToken()
        find_password_obj.find_user_id = find_object.first().id
        find_password_obj.find_user_email = find_email
        find_password_obj.uuid = uuid_string
        find_password_obj.find_expired_date = expire_date
        db_session.add(find_password_obj)

        # 해당되는 이름 가져오기
        user_object = db_session.query(User).filter(User.username == find_username,
                                                   User.email == find_email,
                                                   User.name == find_name).first()

        # 해당되는 Email 파일을 오픈 후 메일 주소의 이름과 링크만 수정한다.
        # 해당 HTML 파일을 읽어온다
        content = render_template("public/user/mail_password.html",
                                  user_real_name=user_object.name,
                                  uuid=uuid_string)

        # Amazon SES Mail Send
        ses = SESMail("10월의 하늘 비밀번호 초기화 인증", content, [])
        ses.send({"name": find_name, "addr": find_email})

        return jsonify(success=True)
    else:
        # 아닌 경우
        return jsonify(success=False)


@page.route('/find_match_uuid', methods=['GET'])
def find_match_uuid():

    # 해당되는 비밀번호 UUID에 있는 것을 확인
    find_uuid = request.args.get('uuid')

    # 만료일보다 기간이 지나면 해당 인증번호는 사용을 못하게 막아놔야함
    # 첫 비밀번호 확인
    find_match_uuid_object = db_session.query(FindPasswordToken).filter(FindPasswordToken.find_expired_date >= datetime.datetime.now()).order_by(FindPasswordToken.id.desc()).first()
    find_match_password_uuid = find_match_uuid_object.uuid

    if find_password is None:
        # 인증번호가 없는 경우
        return redirect('/')
    else:
        # 인증번호가 존재하고 일치할 경우
        # 해당 인증번호는 1회용으로 사용 예정
        if find_match_password_uuid == find_uuid and find_match_uuid_object.find_email_use_yn is False:
            find_match_uuid_object.find_email_use_yn = True
            return render_template("public/user/reset_password.html", uuid=find_uuid)
        # 인증번호가 존재하나 잘못 입력할 경우
        else:
            return abort(404)


# 인증번호가 맞을시 비밀번호 변경
@page.route('/reset_password')
def reset_password():
    return render_template("public/user/reset_password.html")


# 인증번호가 맞을시 비밀번호 변경
@page.route('/reset_complete_password/<uuid:uuid>', methods=['POST'])
def reset_complete_password(uuid):

    # 해당된 UUID에 일치하는 아이디 찾기
    uuid_object = db_session.query(FindPasswordToken).filter(FindPasswordToken.uuid == str(uuid)).first()
    reset_complete_user = db_session.query(User).filter(User.id == uuid_object.find_user_id).first()

    # 해당된 패스워드를 SHA256 방식으로 변경
    req_json = request.get_json()
    reset_password = req_json.get('reset_password')
    m = hashlib.sha256()
    m.update(reset_password.encode('utf-8'))

    # 해당된 정보를 통해 USERID 변경
    reset_password = m.hexdigest()
    reset_complete_user.password = reset_password
    db_session.add(reset_complete_user)

    return jsonify(success=True)


@page.route("/ot_and_party")
def ot_and_party_status():
    req_json = request.get_json()

    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 현재 유저로 등록된 참석 여부 레코드가 있는지 확인한다.
    ot_party_record = db_session.query(OTandParty).filter(OTandParty.party_user_id == current_user.id,
                                                          OTandParty.roundtable_id == main_roundtable.id).first()
    if not ot_party_record:
        return jsonify(success=True, ot1_join=False, ot2_join=False, party_join=False)
    else:
        return jsonify(
            success=True,
            ot1_join=bool(ot_party_record.ot1_join),
            ot2_join=bool(ot_party_record.ot2_join),
            party_join=bool(ot_party_record.party_join))


@page.route("/ot_and_party", methods=["POST"])
def ot_and_party_update():
    req_json = request.get_json()

    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 현재 유저로 등록된 참석 여부 레코드가 있는지 확인한다.
    ot_party_record = db_session.query(OTandParty).filter(OTandParty.party_user_id == current_user.id).first()
    if not ot_party_record:
        ot_party_record = OTandParty()
        ot_party_record.party_user_id = current_user.id
        ot_party_record.roundtable_id = main_roundtable.id
        db_session.add(ot_party_record)

    if req_json.get('join_type') == 'ot1_join':
        ot_party_record.ot1_join = req_json.get('value')
    elif req_json.get('join_type') == 'ot2_join':
        ot_party_record.ot2_join = req_json.get('value')
    elif req_json.get('join_type') == 'party_join':
        ot_party_record.party_join = req_json.get('value')

    return jsonify(success=True)


@page.route("/homepage_wallpaper")
def homepage_wallpaper():
    slide_carousel = SlideCarousel.query.order_by(asc(SlideCarousel.id)).first()
    wallpaper_mime = mimetypes.guess_type(s3_object_url(slide_carousel.slide_img))

    req = requests.get(s3_object_url(slide_carousel.slide_img))
    resp = make_response(req.content)
    resp.headers['Content-Type'] = wallpaper_mime[0]
    resp.headers['Content-Length'] = req.headers['Content-Length']
    resp.headers['Last-Modified'] = datetime.datetime.now()
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '-1'

    return resp


@page.route('/librarian_reg', methods=['POST'])
def librarian_reg():
    req_json = request.get_json()

    library_record = Library.query.filter(Library.id == req_json.get('library_id')).first()
    user_record = User.query.filter(User.id == current_user.id).first()

    # 도서관의 사서 이메일 주소와 사용자의 이메일 주소가 같은지 한번 더 확인한다(관리 권한을 부여하기 때문에 2중
    # 보안을 한다..

    if library_record.manager_email == current_user.email:
        user_record.usertype = 'B'
        user_record.library = library_record

        return jsonify(success=True)

    return jsonify(success=False, msg='너무 하시는거 아니에요?')


@page.app_context_processor
def public_context_processor():
    return {
        "library_sessions": library_sessions,
        "library_short2long": short2long_name,
        'modified_allow_date': modified_allow_date,
        'dir': dir,
        "latest_is_donation": latest_is_donation,
        "shortcut_summary": shortcut_summary
    }


@page.app_template_filter('donation_type')
def donation_type(s):
    return dict(A="도서 기부", B='뒷풀이 기부').get(s, '')


@page.app_template_filter('donation_transport')
def donation_transport(s):
    return dict(A="택배, 방문 등으로 미리 전달하겠습니다", B='뒷풀이 장소 등에 직접 가져갑니다').get(s, '')


@page.app_template_filter('library_find')
def library_find(party_user, roundtable):
    lectures = tuple(filter(lambda item: item.roundtable == roundtable, party_user.lecture))
    hosts = tuple(filter(lambda item: item.roundtable == roundtable, party_user.host))

    find_library_name = ''
    if len(lectures):
        find_library_name = lectures[0].library.library_name
    elif len(hosts):
        find_library_name = hosts[0].library.library_name

    return find_library_name


@page.app_template_filter('social_name')
@login_required
def social_name(name):
    return {"google-oauth2": '구글 로그인', 'facebook': '페이스북', 'kakao': '카카오', 'naver': '네이버'}[name]
