from werkzeug.routing import BaseConverter

from nanumlectures.database import db_session
from nanumlectures.models import (Library, User, FAQ, Lecture, SessionHost,
                                  News, Books, Roundtable, PhotoAlbum,
                                  DesignData, DonationGoods, BoardModel)


class LibraryConverter(BaseConverter):
    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(Library).filter(Library.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class UserConverter(BaseConverter):
    def to_python(self, value):
        record = db_session.query(User.username, User.name, User.email, User.phone, User.last_login_date, User.usertype,
                                  Library.id, Library.library_name, User).outerjoin(Library).filter(
            User.username == value).first()

        return record

    def to_url(self, values):
        return str(values)


class UserModelConverter(BaseConverter):
    def to_python(self, value):
        record = db_session.query(User).filter(User.username == value).first()

        return record

    def to_url(self, values):
        return str(values)


class RoundtableConverter(BaseConverter):
    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(Roundtable).filter(Roundtable.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class FAQConverter(BaseConverter):
    """FAQ Converter"""

    def to_python(self, value):
        record = db_session.query(FAQ).filter(FAQ.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class LectureConverter(BaseConverter):
    """강연자 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(Lecture).filter(Lecture.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class SessionHostConverter(BaseConverter):
    """진행자 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(SessionHost).filter(SessionHost.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class NewsConverter(BaseConverter):
    """언론 홍보 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(News).filter(News.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class BooksConverter(BaseConverter):
    """도서 관리 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(Books).filter(Books.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class PhotoConverter(BaseConverter):
    """사진첩 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(PhotoAlbum).filter(PhotoAlbum.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class DesignDataConverter(BaseConverter):
    """디자인 파일 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(DesignData).filter(DesignData.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class GoodsDonationConverter(BaseConverter):
    """물품 기부 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(DonationGoods).filter(DonationGoods.id == value).first()

        return record

    def to_url(self, values):
        return str(values)


class BoardConverter(BaseConverter):
    """준비위 회의록 Model Converter"""

    def to_python(self, value):
        if not value.isdecimal():
            raise ValueError('잘못된 요청입니다.')
        record = db_session.query(BoardModel).filter(BoardModel.id == value).first()

        return record

    def to_url(self, values):
        return str(values)
