import datetime
from functools import wraps, update_wrapper

import user_agents
from flask import request, make_response

from flask_login import current_user
from markupsafe import Markup

from nanumlectures.database import db_session
from nanumlectures.models import User, Roundtable

area_short_name = ('서울', '부산', '인천', '대전', '대구', '울산', '광주', '경기', '강원', '충북', '충남', '전북',
                   '전남', '경북', '경남', '제주도', '세종시', '특별한 도서관')

area_long_name = ('서울특별시', '부산광역시', '인천광역시', '대전광역시', '대구광역시', '울산광역시', '광주광역시',
                  '경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도',
                  '제주특별자치도', '세종특별자치시', '특별한 도서관')

short2long = tuple(zip(area_short_name, area_long_name))
long2short = tuple(zip(area_long_name, area_short_name))


def short2long_name(short_name):
    return tuple(filter(lambda x: x[0] == short_name["name"], short2long))[0][1]


def library2dict(library_record):
    if not library_record:
        return {}

    return dict(
        library_name=library_record.library_name,
        manager_name=library_record.manager_name,
        library_tel=library_record.library_tel,
        library_fax=library_record.library_fax,
        library_homepage=library_record.library_homepage,
        manager_hp=library_record.manager_hp,
        lat=library_record.lat,
        long=library_record.long,
        area=library_record.area,
        library_description=library_record.library_description,
        lib_description=str(library_record.lib_description).replace("<br>", ", "),
        expected_audience=library_record.expected_audience,
        library_addr=library_record.library_addr,
        lecture_video_recording_yn=library_record.lecture_video_recording_yn
    )


def user_lectureAndHostExist(roundtable):
    user = db_session.query(User).filter(User.id == current_user.id).first()

    lecture_count = tuple(filter(lambda item: item.roundtable_id == roundtable.id, user.lecture))
    host_count = tuple(filter(lambda item: item.roundtable_id == roundtable.id, user.host))

    if len(lecture_count) > 0 or len(host_count) > 0:
        return True
    else:
        return False


def donate2record(record, donation_type):
    ret = dict()

    if donation_type == 'lecture' and record:
        ret['id'] = record.id
        ret['roundtable'] = record.roundtable.roundtable_num
        ret['library'] = library2dict(record.library)
        ret['session_time'] = record.session_time
        ret['lecture_title'] = record.lecture_title
        ret['lecture_summary'] = record.lecture_summary
        ret['lecture_expected_audience'] = record.lecture_expected_audience
        ret['lecture_belong'] = record.lecture_belong
        ret['lecture_public_yn'] = record.lecture_public_yn
    elif donation_type == 'host':
        raise NotImplementedError('진행자 수정은 지원하지 않습니다')

    return ret


def modified_allow_date(entry):
    current_year = datetime.datetime.now().strftime('%Y')
    if entry and entry.roundtable:
        entry_date = datetime.datetime(
            year=entry.roundtable.roundtable_date.year,
            month=entry.roundtable.roundtable_date.month,
            day=entry.roundtable.roundtable_date.day,
        )
        entry_year = entry_date.strftime('%Y')

        if current_year != entry_year:
            return False
        elif current_year == entry_year and entry_date > datetime.datetime.now():
            return True
        else:
            return False


def batch_fill(entry, session_time):
    entry = tuple(entry)

    if len(entry) > 0:
        return entry + tuple([None for _ in range(session_time - len(entry))])
    else:
        return [None for _ in range(session_time)]


def line_break(s):
    return s.replace("\n", "<br>")


def statstics_summary(statics_area_cnt, statics_library, special_area=None):
    for library, round_and_library in statics_library:
        library_area = special_area or library.area
        # 지역별로 신청 가능(미신청한 강연/진행자) 수를 긁어온다..(애초에 이게 말이 되니..)
        if library_area in statics_area_cnt:
            statics_area_cnt[library_area]['total_round_num'] += round_and_library.round_num
            statics_area_cnt[library_area]['total_lecture'] += len(library.lecture)
            statics_area_cnt[library_area]['total_host'] += len(library.host)
        else:
            statics_area_cnt[library_area] = dict(
                total_round_num=round_and_library.round_num,
                total_lecture=len(library.lecture),
                total_host=len(library.host)
            )


def latest_is_donation():
    # 최근 회차 정보 가져오기
    main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

    # 로그인 중인 사용자가 현재 회차에 강연 또는 진행을 신청했는지 살펴보고 하나라도 신청한 경우 True를 반복한다.
    lectures = tuple(filter(lambda item: item.roundtable == main_roundtable, current_user.lecture))
    hosts = tuple(filter(lambda item: item.roundtable == main_roundtable, current_user.host))

    if len(lectures) or len(hosts):
        return True
    else:
        return False


def shortcut_summary(value, lecture_name):
    lecture_summary_cut = 180

    if len(lecture_name) > 33:
        lecture_summary_cut = 150

    if len(value) > lecture_summary_cut:
        summary_beofre, summary_after = value[:lecture_summary_cut], value[lecture_summary_cut:]
        more_tag = '<i class="fas fa-plus-square"></i>'
        a_tag = ('<a href="#" onclick="event.preventDefault();"'
                 ' data-toggle="tooltip" data-placement="bottom" title="{}">{}</a>').format(summary_after, more_tag)
        
        return Markup(summary_beofre + "&nbsp;{}".format(a_tag))
    return value


def is_ie_browser():
    connected_agent = user_agents.parse(request.user_agent.string)
    return connected_agent.browser.family == "IE"


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)