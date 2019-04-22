import hashlib

from flask_login import UserMixin
from sqlalchemy import (Column, BigInteger, Sequence, String, Text, Boolean,
                        DateTime, func, Integer, Date, Float, Table, ForeignKey)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, column_property

from nanumlectures.database import Base, db_session
from social_flask_sqlalchemy.models import UserSocialAuth


class User(Base, UserMixin):
    """사용자"""
    __tablename__ = 'users'

    id = Column(BigInteger, Sequence('user_seq'), primary_key=True)
    name = Column(String(100), comment='사용자명')
    description = Column(Text, comment='부가 설명')
    phone = Column(String(100), comment='전화번호')
    email = Column(String(100), comment='이메일')
    username = Column(String(100), comment='사용자 ID')
    password = Column(String(100), comment='사용자 비밀번호')
    usertype = Column(String(1), default='C', comment='사용자 타입: 슈퍼 유저, 도서관, 일반 유저')
    last_login_date = Column(DateTime, comment='최종 로그인 일자')
    social_user_yn = Column(String(1), default='N', comment='소셜 유저 여부')
    expired_date = Column(DateTime, default=None, comment='계정 만료 기간')
    created_date = Column(DateTime, default=func.now(), comment="생성일자")
    modified_date = Column(DateTime, default=func.now(), comment="수정일자")
    library = relationship("Library", uselist=False)
    lecture = relationship("Lecture", back_populates="lecture_user")
    host = relationship("SessionHost", back_populates="host_user")
    phone_search = column_property(func.replace(phone, '-', ''))
    # social_info = relationship("UserSocialAuth", backref="user")

    def __repr__(self):
        r = {
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'last_login': self.last_login_date
        }
        return str(r)

    def __iter__(self):
        for entry in ['name']:
            yield entry, getattr(self, entry, '')

    def can_login(self, password):
        m = hashlib.sha256()
        m.update(password.encode('utf-8'))
        return self.password == m.hexdigest()

    @hybrid_property
    def is_active(self):
        return True

    @hybrid_property
    def is_authenticated(self):
        return True

    def get_id(self):
        return self.username

    @hybrid_property
    def is_anonymous(self):
        return False

    def set_password(self, new_password):
        m = hashlib.sha256()
        m.update(new_password.encode('utf-8'))
        self.password = m.hexdigest()


class RoundtableAndLibrary(Base):
    __tablename__ = 'roundtable_library'

    library_id = Column(Integer, ForeignKey('library_mngt.id'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'), primary_key=True)
    round_num = Column(Integer, comment='세션 수')
    library = relationship("Library", back_populates="roundtable")
    roundtable = relationship("Roundtable", back_populates="library")


class Roundtable(Base):
    __tablename__ = 'roundtable_mngt'

    id = Column(Integer, Sequence('roundtable_seq'), primary_key=True)
    roundtable_num = Column(Integer, comment='개최회차')
    roundtable_year = Column(Integer, comment='개최년도')
    roundtable_date = Column(Date, comment='개최일')
    staff = Column(Text, comment='준비위원회 사람들')
    library = relationship("RoundtableAndLibrary", back_populates="roundtable")
    lecture = relationship("Lecture", back_populates="roundtable")
    host = relationship("SessionHost", back_populates="roundtable")

    @hybrid_property
    def library_modify_list(self):
        return [dict(
                library=dict(id=entry.library.id,
                library_name=entry.library.library_name,
                library_addr=entry.library.library_addr),
            session_time=entry.round_num) for entry in self.library]

    @hybrid_property
    def reg_available_library(self):
        return [dict(
            id=entry.library.id,
            library_name=entry.library.library_name,
            library_addr=entry.library.library_addr,
            session_time=entry.round_num) for entry in self.library]


class Library(Base):
    """도서관"""
    __tablename__ = 'library_mngt'

    id = Column(Integer, Sequence('library_seq'), primary_key=True)
    library_name = Column(String(60), comment='도서관명')
    manager_name = Column(String(60), comment='담당자명')
    manager_id = Column(Integer, ForeignKey('users.id'), comment='담당자 ID')
    library_tel = Column(String(50), comment='대표전화')
    library_fax = Column(String(50), comment='팩스')
    library_homepage = Column(String(100), comment='홈페이지')
    manager_hp = Column(String(50), comment='휴대전화')
    lat = Column(Float, comment='위도')
    long = Column(Float, comment='경도')
    area = Column(String(10), comment='권역')
    library_description = Column(Text, comment='강연장 환경')
    expected_audience = Column(String(255), comment='예상 청중')
    library_addr = Column(String(255), comment='도서관 주소')
    daum_place_id = Column(String(20), comment="DAUM 지도 Place ID")
    daum_place_url = Column(String(255), comment="DAUM 지도 Place URL")
    roundtable = relationship("RoundtableAndLibrary", back_populates="library")
    lecture = relationship("Lecture", back_populates="library")
    host = relationship("SessionHost", back_populates="library")


class FAQ(Base):
    """FAQ"""
    __tablename__ = 'faq'

    id = Column(Integer, Sequence('faq_seq'), primary_key=True)
    classify = Column(String(20), comment='유형')
    subject = Column(String(255), comment='제목')
    body = Column(Text, comment='본문')
    writer_id = Column(Integer, ForeignKey('users.id'), comment='FAQ 작성자 ID')
    writer = relationship("User")
    write_date = Column(Date, default=func.now(), comment='작성일')


class Lecture(Base):
    """강연기부"""
    __tablename__ = 'lecture'

    id = Column(Integer, Sequence('lecture_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'), comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable", back_populates="lecture")
    library_id = Column(Integer, ForeignKey('library_mngt.id'), comment='도서관 고유번호')
    library = relationship('Library', back_populates="lecture")
    session_time = Column(Integer, comment="강연시간")
    lecture_title = Column(String(100), comment='강연제목')
    lecture_summary = Column(Text, comment='강연개요')
    lecture_expected_audience = Column(String(255), comment='예상 청중')
    lecture_user_id = Column(Integer, ForeignKey('users.id'), comment='강연자 ID')
    lecture_user = relationship("User", back_populates="lecture")
    lecture_name = Column(String(30), comment='강연자명')
    lecture_belong = Column(String(100), comment='소속')
    lecture_hp = Column(String(50), comment='휴대폰')
    lecture_email = Column(String(50), comment='이메일')
    lecture_public_yn = Column(Boolean, default=False, comment='공개 여부')
    lecture_use_yn = Column(Boolean, default=True, comment='확정 여부')

    @hybrid_property
    def session_host(self):
        host_record = db_session.query(SessionHost).filter(
            SessionHost.roundtable_id == self.roundtable_id,
            SessionHost.library_id == self.library_id,
            SessionHost.session_time == self.session_time).first()

        return host_record

    @hybrid_property
    def lecture_info(self):
        ret = [self.lecture_name]
        if self.lecture_email:
            ret.append('({0})'.format(self.lecture_email))
        if self.lecture_belong:
            ret.append(' - {0}'.format(self.lecture_belong))

        return ''.join(ret)


class SessionHost(Base):
    """진행 기부"""
    __tablename__ = 'session_host'

    id = Column(Integer, Sequence('host_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'), comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable", back_populates="host")
    library_id = Column(Integer, ForeignKey('library_mngt.id'), comment='도서관 고유번호')
    library = relationship('Library', back_populates="host")
    session_time = Column(Integer, comment="강연시간")
    host_user_id = Column(Integer, ForeignKey('users.id'), comment='진행자 ID')
    host_user = relationship("User", back_populates="host")
    host_name = Column(String(30), comment='진행자명')
    host_belong = Column(String(100), comment='소속')
    host_hp = Column(String(50), comment='휴대폰')
    host_email = Column(String(50), comment='이메일')
    host_use_yn = Column(Boolean, default=True, comment='확정 여부')

    @hybrid_property
    def host_info(self):
        ret = [self.host_name]
        if self.host_email:
            ret.append('({0})'.format(self.host_email))
        if self.host_belong:
            ret.append(' - {0}'.format(self.host_belong))

        return ''.join(ret)


class News(Base):
    """언론 홍보"""
    __tablename__ = 'news'

    id = Column(Integer, Sequence('news_seq'), primary_key=True)
    category = Column(Integer, comment='구분')
    press_date = Column(Date, comment='배부일자')
    news_title = Column(String(100), comment='언론제목')
    news_press = Column(String(100), comment='언론사')
    news_link = Column(String(400), comment='기사링크')
    news_body = Column(Text, comment='본문')
    news_write_date = Column(Date, default=func.now(), comment='작성일자')
    writer_id = Column(Integer, ForeignKey('users.id'), comment='뉴스 작성자 ID')
    writer = relationship("User")


class PhotoAlbum(Base):
    """사진첩 관리"""
    __tablename__ = 'photo_album'

    id = Column(Integer, Sequence('photo_album_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'),
                           comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable")
    album_name = Column(String(255), comment='사진첩명')
    album_link = Column(Text, comment='사진첩 링크(구글 사진첩)')
    representation_image_link = Column(Text, comment='사진첩 대표 이미지(구글 사진첩)')
    album_description = Column(Text, comment='사진첩 설명')
    news_write_date = Column(Date, default=func.now(), comment='작성일자')


class DesignData(Base):
    """디자인 파일"""
    __tablename__ = 'design_data'

    id = Column(Integer, Sequence('design_data_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'),
                           comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable")
    design_name = Column(Text, comment='디자인명')
    design_files = Column(JSON, comment='디자인 파일')
    design_description = Column(Text, comment='디자인 설명')
    design_write_date = Column(Date, default=func.now(), comment='작성일자')


class Books(Base):
    """도서"""
    __tablename__ = 'books'

    id = Column(Integer, Sequence('books_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'),
                           comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable")
    books_title = Column(String(60), comment='도서명')
    books_link = Column(String(400), comment="도서이미지 링크")
    books_isbn = Column(String(50), comment='ISBN')
    books_date = Column(Date, comment='출간일')
    books_company = Column(String(100), default='청어람출판사', comment='출판사')
    books_body = Column(Text, comment='도서 설명')
    books_bookshop = Column(JSON, comment='서점별 링크')


class PageTemplate(Base):
    """웹 페이지 템플릿"""
    __tablename__ = 'web_pages'

    id = Column(Integer, Sequence('pages_seq'), primary_key=True)
    page_name = Column(String(255), comment='페이지 이름')
    page_content = Column(Text, comment='페이지 내용(HTML)')
