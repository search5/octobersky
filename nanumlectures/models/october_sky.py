import hashlib

from flask_login import UserMixin
from markupsafe import Markup
from sqlalchemy import (Column, BigInteger, Sequence, String, Text, Boolean,
                        DateTime, func, Integer, Date, Float, ForeignKey)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, column_property

from nanumlectures.database import Base, db_session


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
    donation = relationship("DonationGoods", back_populates="lecture_user")
    vote = relationship("VoteBooks", back_populates="lecture_user")
    phone_search = column_property(func.replace(phone, '-', ''))

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
    library_type = Column(String(100), comment='일반/SF/장애인/다문화 중 하나')
    library = relationship("Library", back_populates="roundtable")
    roundtable = relationship("Roundtable", back_populates="library")


class Roundtable(Base):
    __tablename__ = 'roundtable_mngt'

    id = Column(Integer, Sequence('roundtable_seq'), primary_key=True)
    roundtable_num = Column(Integer, comment='개최회차')
    roundtable_year = Column(Integer, comment='개최년도')
    roundtable_date = Column(Date, comment='개최일')
    staff = Column(Text, comment='준비위원회 사람들')
    is_active = Column(Boolean, comment='활성화 여부(활성화하면 이게 메인 회차)')
    library = relationship("RoundtableAndLibrary", back_populates="roundtable")
    lecture = relationship("Lecture", back_populates="roundtable")
    host = relationship("SessionHost", back_populates="roundtable")

    @hybrid_property
    def library_modify_list(self):
        return [
            dict(library=dict(id=entry.library.id,
                              library_name=entry.library.library_name,
                              library_addr=entry.library.library_addr),
                 session_time=entry.round_num,
                 library_type=entry.library_type) for entry in self.library]

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
    expected_listens = Column(String(20), comment='예상 인원')
    library_addr = Column(String(255), comment='도서관 주소')
    daum_place_id = Column(String(20), comment="DAUM 지도 Place ID")
    daum_place_url = Column(String(255), comment="DAUM 지도 Place URL")
    manager_email = Column(String(255), comment='담당자 이메일 주소')
    manager_description = Column(String(255), comment='담당자 소속 등')
    library_place = Column(String(255), comment='개최장소')
    place_seats = Column(String(30), comment='개최장소 좌석 수')
    pr_production = Column(Text, comment='홍보물 제작 계획')
    projector_screen = Column(Boolean, comment='빔프로젝터+스크린')
    projector_notebook = Column(Boolean, comment='빔프로젝터에 연결된 노트북')
    sound_equipment = Column(Boolean, comment='음향(마이크. 스피커)')
    etc_equipment = Column(Text, comment='기타 보유')
    camcorder_yn = Column(Boolean, comment='캠코더 보유 유무')
    internet_yn = Column(Boolean, comment='인터넷 보유 유무')
    lecture_video_recording_yn = Column(Boolean, comment='강연 내용 촬영 및 공개 가능 여부')
    coordinate_photography_yn = Column(Boolean, comment='촬영 인력 협조가능 여부')
    roundtable = relationship("RoundtableAndLibrary", back_populates="library")
    lecture = relationship("Lecture", back_populates="library")
    host = relationship("SessionHost", back_populates="library")

    @hybrid_property
    def expected_listener(self):
        return "{}({})".format(self.expected_audience, self.expected_listens)

    @hybrid_property
    def lib_description(self):
        addition = []
        if self.projector_screen:
            addition.append("빔 프로젝터, 스크린")
        if self.projector_notebook:
            addition.append("노트북")
        if self.sound_equipment:
            addition.append("스피커, 마이크")
        if self.camcorder_yn:
            addition.append("캠코더")
        if self.internet_yn:
            addition.append("인터넷")
        if self.etc_equipment:
            addition.append(self.etc_equipment)

        return Markup("{}({})<br>{}".format(self.library_place,
                                            self.place_seats,
                                            "{} 사용 가능".format(", ".join(addition))))


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
        ret = [self.lecture_name or '관리자확인']
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
        ret = [self.host_name or '관리자확인']
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
    album_id = Column(Text, comment='사진첩 ID')
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


class SlideCarousel(Base):
    __tablename__ = 'slide_carousel'

    id = Column(Integer, Sequence('carousel_seq'), primary_key=True)
    slide_num = Column(Integer, comment='슬라이드 번호')
    slide_img_type = Column(String(30), comment='이미지 타입')
    slide_img = Column(Text, comment='슬라이드 이미지')
    slide_title = Column(Text, comment='슬라이드 대표 텍스트')
    slide_text = Column(Text, comment='슬라이드 설명 텍스트')
    is_active = Column(Boolean, comment='활성화 여부')


class VoteBooks(Base):
    __tablename__ = 'vote_books'

    id = Column(Integer, Sequence('vote_books_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'),
                           comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable")
    lecture_user_id = Column(Integer, ForeignKey('users.id'), comment='강연자 ID')
    lecture_user = relationship("User")
    lecture_id = Column(Integer, ForeignKey('lecture.id'), comment='강연 ID')
    lecture = relationship("Lecture")
    book_info = Column(JSON, comment='추천도서 정보')
    enter_path = Column(String(50), comment='진입경로', doc='아 증말!!!, 내가 효용성을 증명해준다(도서문화재단 씨앗 요청)')

    def __iter__(self):
        yield 'book_info', self.book_info

    @hybrid_property
    def disp_book_info(self):
        base_text_format = "<span class=\"font-weight-bold\">{}: </span> <span>{}</span><br>"
        base2_text_format = "<span class=\"font-weight-bold\">{}: </span>"

        book_info_str = [base_text_format.format("추천하고 싶은 도서", self.book_info['book1']),
                         base_text_format.format("추천하고 싶은 이유", self.book_info['book1_desc'])]
        if self.book_info['book2'] or self.book_info['book3']:
            book_info_str.append(base2_text_format.format("그 외에 추천하고 싶은 도서가 있다면 남겨주세요"))
            book_info_str.append("<ul>")
            if self.book_info['book2']:
                book_info_str.append("<li>{}</li>".format(self.book_info['book2']))
            if self.book_info['book3']:
                book_info_str.append("<li>{}</li>".format(self.book_info['book3']))
            book_info_str.append("</ul>")
        if self.book_info['etc']:
            book_info_str.append(base_text_format.format("강연 시에 청중들에게 나눠드릴 책", self.book_info['etc']))
        return ''.join(book_info_str)


class DonationGoods(Base):
    __tablename__ = "donation_goods"

    id = Column(Integer, Sequence('donation_goods_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'),
                           comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable")
    lecture_user_id = Column(Integer, ForeignKey('users.id'), comment='기부자 ID')
    lecture_user = relationship("User")
    donation_type = Column(String(10), comment='기부타입(A: 물품(굿즈)기부, B: 뒷풀이 기부)')
    donation_description = Column(Text, comment='기부 물품 정보')
    donation_transport = Column(String(10), comment='전송수단(A: 미리 전달, B: 현장 전달)')
    is_received = Column(Boolean, comment='물품 수신여부 확인')

    def __iter__(self):
        for item in ('id', 'roundtable_id', 'lecture_user_id', 'donation_type', 'donation_description', 'donation_transport'):
            if item == 'donation_transport':
                yield 'donation_transport_type', getattr(self, item)
            else:
                yield item, getattr(self, item)

    def __lt__(self, other):
        return self.id < other.id


class GoogleToken(Base):
    """구글 웹 인증 토큰 저장(항상 1개 레코드)"""

    __tablename__ = 'google_token'

    id = Column(Integer, Sequence('google_token_seq'), primary_key=True)
    token_content = Column(Text, comment='토큰 내용')


class FindPasswordToken(Base):
    """비밀번호 초기화 및 찾기 테이블"""

    __tablename__ = 'find_password_token'

    id = Column(Integer, Sequence('find_password_token_seq'), primary_key=True)
    find_user_id = Column(Integer, comment='비밀번호 찾는 사람 ID')
    find_user_email = Column (String(100), comment='비밀번호 찾는 사람 이메일')
    uuid = Column(String(50), comment='이메일로 보내지는 Randomstring')
    find_created_date = Column(DateTime, default=func.now(), comment="발급 시간")
    find_expired_date = Column(DateTime, default=None, comment='만료 시간')
    find_email_use_yn = Column(Boolean, default=False, comment='사용 여부')


class BoardModel(Base):
    """게시판 모델"""

    __tablename__ = 'board'

    # board_type이 A1은 준비위 회의록
    # board_type을 따로 두는건.. 또 게시판 추가해달라고 할까봐

    id = Column(Integer, Sequence('board_seq'), primary_key=True)
    board_type = Column(String(50), default='A1', comment='게시판 구분')
    title = Column(String(255), comment='게시판 제목')
    content = Column(Text, comment='게시판 내용')
    wdate = Column(Date, comment='작성일')
    mdate = Column(Date, comment='수정일')
    user_id = Column(Integer, ForeignKey('users.id'), comment='강연자 ID')
    user = relationship("User")
    hit = Column(Integer, comment='조회수', doc='아이고 의미음따..')


class MailSend(Base):
    '''관리자에서 메일 전송'''

    __tablename__ = 'mail_send'

    id = Column(Integer, Sequence('mail_send_seq'), primary_key=True)
    receive_type = Column(String(1), comment='받는 사람 타입')
    receive_addr = Column(JSON, comment='받는 사람 메일 주소(도서관 섭외 한정)')
    mail_subject = Column(String(255), comment='메일 제목')
    mail_content = Column(Text, comment='메일 본문')
    mail_attach = Column(JSON, comment='첨부파일 목록', doc='(S3에 저장하자...) 근데 첨부파일을 저장할 필요가 있나.. 앗흥..')
    uploading_file_cnt = Column(Integer, comment='업로드 중인 파일 갯수')
    uploaded_file_cnt = Column(Integer, comment='업로드할 파일 갯수')
    is_mail_send = Column(Boolean, comment='메일 발송 여부')
    send_time = Column(DateTime, comment='메일 발송 시간')


class OTandParty(Base):
    '''OT 및 뒤풀이 참석 여부 결정'''
    __tablename__ = 'ot_and_party'

    id = Column(Integer, Sequence('ot_and_party_seq'), primary_key=True)
    roundtable_id = Column(Integer, ForeignKey('roundtable_mngt.id'),
                           comment="회차 고유번호(DB 고유 인덱스)")
    roundtable = relationship("Roundtable")
    party_user_id = Column(Integer, ForeignKey('users.id'), comment='기부자 ID')
    party_user = relationship("User")
    ot1_join = Column(Boolean, default=False, comment='1차 OT 참석 여부',)
    ot2_join = Column(Boolean, default=False, comment='2차 OT 참석 여부')
    party_join = Column(Boolean, default=False, comment='뒤풀이 참석 여부')
