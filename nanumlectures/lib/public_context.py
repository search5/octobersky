import datetime

from flask_login import current_user

from nanumlectures.database import db_session
from nanumlectures.models import User

area_short_name = ('서울', '부산', '인천', '대전', '대구', '울산', '광주', '경기', '강원', '충북', '충남', '전북',
                   '전남', '경북', '경남', '제주특별자치도', '세종특별자치시')

area_long_name = ('서울특별시', '부산광역시', '인천광역시', '대전광역시', '대구광역시', '울산광역시', '광주광역시',
                  '경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도',
                  '제주특별자치도', '세종특별자치시')

short2long = tuple(zip(area_short_name, area_long_name))
long2short = tuple(zip(area_long_name, area_short_name))


def short2long_name(short_name):
    return tuple(filter(lambda x: x[0] == short_name, short2long))[0][1]


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
        expected_audience=library_record.expected_audience,
        library_addr=library_record.library_addr
    )


def user_lectureAndHostExist(roundtable_id):
    user = db_session.query(User).filter(User.id == current_user.id).first()

    lecture_count = tuple(filter(lambda item: item.roundtable_id == roundtable_id[0], user.lecture))
    host_count = tuple(filter(lambda item: item.roundtable_id == roundtable_id[0], user.host))

    if len(lecture_count) > 0 or len(host_count) > 0:
        return True
    else:
        return False


def donate2record(record, donation_type):
    ret = dict()

    if donation_type == 'lecture':
        ret['id'] = record.id
        ret['roundtable'] = record.roundtable.roundtable_num
        ret['library'] = library2dict(record.library)
        ret['session_time'] = record.session_time
        ret['lecture_title'] = record.lecture_title
        ret['lecture_summary'] = record.lecture_summary
        ret['lecture_expected_audience'] = record.lecture_expected_audience
        ret['lecture_public_yn'] = record.lecture_public_yn
    elif donation_type == 'host':
        raise NotImplementedError('진행자 수정은 지원하지 않습니다')

    return ret


def modifed_allow_date(entry):
    current_year = datetime.datetime.now().strftime('%Y')
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
