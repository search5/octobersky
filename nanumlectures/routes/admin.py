import datetime
import os

import google_auth_oauthlib.flow
import google_auth_oauthlib.helpers
import yaml
from flask import Blueprint, url_for, session, redirect, request

from nanumlectures.lib.public_context import library2dict, area_short_name
from nanumlectures.models import GoogleToken, db_session
from nanumlectures.routes.admin_views.board_view import BoardListView, BoardRegView, BoardEditView, BoardDetailView
from nanumlectures.routes.admin_views.books_view import (
    BooksListView, BooksRegView, BooksEditView, BooksDetailView, BookFindNaverAPI)
from nanumlectures.routes.admin_views.dashboard_view import DashboardView
from nanumlectures.routes.admin_views.design_view import (
    DesignListView, DesignRegView, DesignEditView,
    DesignDetailView, DesignFileDownloadView)
from nanumlectures.routes.admin_views.donate_view import (
    DonateEditView, DonatePreviewView)
from nanumlectures.routes.admin_views.faq_view import (
    FaqListView, FaqRegView, FaqEditView, FaqDetailView)
from nanumlectures.routes.admin_views.goods_donate_view import GoodsDonateListView, GoodsDonateRegView, \
    GoodsDonateEditView, GoodsDonateDetailView, GoodsDonateCsvView, GoodsDonateCheckView
from nanumlectures.routes.admin_views.host_view import (
    SessionHostRegView, SessionHostEditView,
    SessionHostDetailView, SessionHostListView)
from nanumlectures.routes.admin_views.lecture_view import (
    LectureRegView, LectureEditView, LectureDetailView,
    LectureListView, LectureFindView)
from nanumlectures.routes.admin_views.library_view import (
    LibraryRegView, LibraryEditView, LibraryDetailView,
    LibraryListView, LibrarySearchView, LibraryOwnerView)
from nanumlectures.routes.admin_views.mail_admin_view import MailSendView, \
    MailAttachSend
from nanumlectures.routes.admin_views.main_admin_view import MainAdminView
from nanumlectures.routes.admin_views.member_view import (
    MemberDetailView, MemberEditView, MemberList, MemberPasswordResetView)
from nanumlectures.routes.admin_views.news_view import (
    NewsListView, NewsRegView, NewsDetailView, NewsEditView)
from nanumlectures.routes.admin_views.otnparty_view import OTAndPartyView, OTAndPartyCsvView
from nanumlectures.routes.admin_views.photo_view import (
    PhotoListView, PhotoRegView, PhotoDetailView, PhotoEditView)
from nanumlectures.routes.admin_views.roundtable_view import (
    RoundtableRegView, RoundtableDetailView,
    RoundtableEditView, RoundtableListView, RoundtableActiveView)
from nanumlectures.routes.admin_views.vote_books_view import VoteBooksListView, VoteBooksListCsvView
from nanumlectures.settings import CLIENT_SECRET

page = Blueprint('admin', __name__, url_prefix="/admin", static_folder='../static/admin', static_url_path='/static')

dashboard_view = DashboardView.as_view('dashboard')
page.add_url_rule('/dashboard', view_func=dashboard_view)

otandparty_view = OTAndPartyView.as_view('otandparty')
page.add_url_rule('/otandparty', view_func=otandparty_view)

otandparty_csv_view = OTAndPartyCsvView.as_view('otandparty_csv')
page.add_url_rule('/otandparty/download', view_func=otandparty_csv_view, methods=['GET'])

roundtable_list_view = RoundtableListView.as_view('roundtable_list')
page.add_url_rule('/roundtable/list', view_func=roundtable_list_view)

roundtable_reg_view = RoundtableRegView.as_view('roundtable_reg')
page.add_url_rule('/roundtable/reg', view_func=roundtable_reg_view)

roundtable_detail_view = RoundtableDetailView.as_view('roundtable_view')
page.add_url_rule('/roundtable/<roundtable:round>', view_func=roundtable_detail_view)

roundtable_edit_view = RoundtableEditView.as_view('roundtable_edit')
page.add_url_rule('/roundtable/<roundtable:round>/edit', view_func=roundtable_edit_view)

roundtable_active_view = RoundtableActiveView.as_view('roundtable_active_view')
page.add_url_rule('/roundtable/active', view_func=roundtable_active_view, methods=['POST'])

lecture_list_view = LectureListView.as_view('lecturer')
page.add_url_rule('/lecturer', view_func=lecture_list_view)

lecture_find_view = LectureFindView.as_view('lecture_find')
page.add_url_rule('/lecturer/find', view_func=lecture_find_view)

lecture_reg_view = LectureRegView.as_view('lecturer_reg')
page.add_url_rule('/lecturer/reg', view_func=lecture_reg_view)

lecture_edit_view = LectureEditView.as_view('lecturer_edit')
page.add_url_rule('/lecturer/<lecturer:lecturer>/edit', view_func=lecture_edit_view)

lecture_detail_view = LectureDetailView.as_view('lecturer_view')
page.add_url_rule('/lecturer/<lecturer:lecturer>', view_func=lecture_detail_view)

library_search_view = LibrarySearchView.as_view('library_search')
page.add_url_rule('/library/search', view_func=library_search_view)

library_list_view = LibraryListView.as_view('library_list')
page.add_url_rule('/library', view_func=library_list_view)

library_reg_view = LibraryRegView.as_view('library_reg')
page.add_url_rule('/library/reg', view_func=library_reg_view)

library_edit_view = LibraryEditView.as_view('library_edit')
page.add_url_rule('/library/<library:library>/edit', view_func=library_edit_view)

library_owner_view = LibraryOwnerView.as_view('library_mngt')
page.add_url_rule('/library/owner', view_func=library_owner_view)

library_detail_view = LibraryDetailView.as_view('library_view')
page.add_url_rule('/library/<library:library>', view_func=library_detail_view)

session_host_list_view = SessionHostListView.as_view('session_host')
page.add_url_rule('/session_host', view_func=session_host_list_view)

session_host_reg_view = SessionHostRegView.as_view('session_host_reg')
page.add_url_rule('/session_host/reg', view_func=session_host_reg_view)

session_host_edit_view = SessionHostEditView.as_view('session_host_edit')
page.add_url_rule('/session_host/<host:host>/edit', view_func=session_host_edit_view)

session_host_detail_view = SessionHostDetailView.as_view('session_host_view')
page.add_url_rule('/session_host/<host:host>', view_func=session_host_detail_view)

member_list_view = MemberList.as_view('member_list')
page.add_url_rule('/member/', view_func=member_list_view, methods=['GET'])

member_detail_view = MemberDetailView.as_view('member_view')
page.add_url_rule('/member/<user:uid>', view_func=member_detail_view, methods=['GET'])
page.add_url_rule('/member/<user_model:uid>', view_func=member_detail_view, methods=['DELETE'])

member_edit_view = MemberEditView.as_view('member_edit')
page.add_url_rule('/member/<user:uid>/edit', view_func=member_edit_view, methods=['GET'])
page.add_url_rule('/member/<user_model:uid>/edit', view_func=member_edit_view, methods=['POST'])

member_password_view = MemberPasswordResetView.as_view('member_password_reset')
page.add_url_rule('/member/<user_model:uid>/reset', view_func=member_password_view, methods=['POST'])

nesw_list_view = NewsListView.as_view('news')
page.add_url_rule('/news/', view_func=nesw_list_view, methods=['GET'])

news_reg_view = NewsRegView.as_view('news_reg')
page.add_url_rule('/news/reg', view_func=news_reg_view)

news_edit_view = NewsEditView.as_view('news_edit')
page.add_url_rule('/news/<news:news>/edit', view_func=news_edit_view)

news_detail_view = NewsDetailView.as_view('news_view')
page.add_url_rule('/news/<news:news>', view_func=news_detail_view)

faq_list_view = FaqListView.as_view('faq')
page.add_url_rule('/faq/', view_func=faq_list_view, methods=['GET'])

faq_reg_view = FaqRegView.as_view('faq_reg')
page.add_url_rule('/faq/reg', view_func=faq_reg_view)

faq_edit_view = FaqEditView.as_view('faq_edit')
page.add_url_rule('/faq/<faq:faq>/edit', view_func=faq_edit_view)

faq_detail_view = FaqDetailView.as_view('faq_view')
page.add_url_rule('/faq/<faq:faq>', view_func=faq_detail_view)

photo_list_view = PhotoListView.as_view('photo')
page.add_url_rule('/photo/', view_func=photo_list_view, methods=['GET'])

photo_reg_view = PhotoRegView.as_view('photo_reg')
page.add_url_rule('/photo/reg', view_func=photo_reg_view)

photo_edit_view = PhotoEditView.as_view('photo_edit')
page.add_url_rule('/photo/<photo:photo>/edit', view_func=photo_edit_view)

photo_detail_view = PhotoDetailView.as_view('photo_view')
page.add_url_rule('/photo/<photo:photo>', view_func=photo_detail_view)

design_list_view = DesignListView.as_view('design')
page.add_url_rule('/design/', view_func=design_list_view, methods=['GET'])

design_reg_view = DesignRegView.as_view('design_reg')
page.add_url_rule('/design/reg', view_func=design_reg_view)

design_edit_view = DesignEditView.as_view('design_edit')
page.add_url_rule('/design/<design:design>/edit', view_func=design_edit_view)

design_detail_view = DesignDetailView.as_view('design_view')
page.add_url_rule('/design/<design:design>', view_func=design_detail_view)

design_download_view = DesignFileDownloadView.as_view('design_download')
page.add_url_rule('/design/<design:design>/<filename>', view_func=design_download_view)

book_list_view = BooksListView.as_view('books')
page.add_url_rule('/books/', view_func=book_list_view, methods=['GET'])

book_reg_view = BooksRegView.as_view('books_reg')
page.add_url_rule('/books/reg', view_func=book_reg_view)

book_edit_view = BooksEditView.as_view('books_edit')
page.add_url_rule('/books/<book:book>/edit', view_func=book_edit_view)

book_detail_view = BooksDetailView.as_view('books_view')
page.add_url_rule('/books/<book:book>', view_func=book_detail_view)

book_naver_view = BookFindNaverAPI.as_view('books_naver_view')
page.add_url_rule('/books/find/naver', view_func=book_naver_view)

vote_book_list_view = VoteBooksListView.as_view('vote_books')
page.add_url_rule('/vote_books/', view_func=vote_book_list_view, methods=['GET'])

vote_book_csv_view = VoteBooksListCsvView.as_view('vote_books_csv')
page.add_url_rule('/vote_books/csv', view_func=vote_book_csv_view, methods=['GET'])

donate_edit_view = DonateEditView.as_view('donate_edit')
page.add_url_rule('/donate', view_func=donate_edit_view)

donate_preview_view = DonatePreviewView.as_view('donate_preview')
page.add_url_rule('/donate/preview', view_func=donate_preview_view)

goods_donation_view = GoodsDonateListView.as_view('goods_donation')
page.add_url_rule('/goods_donate', view_func=goods_donation_view)

goods_donation_reg_view = GoodsDonateRegView.as_view('goods_donation_reg')
page.add_url_rule('/goods_donate/reg', view_func=goods_donation_reg_view)

goods_donation_edit_view = GoodsDonateEditView.as_view('goods_donation_edit')
page.add_url_rule('/goods_donate/<donation:donation>/edit', view_func=goods_donation_edit_view)

goods_donation_detail_view = GoodsDonateDetailView.as_view('goods_donation_view')
page.add_url_rule('/goods_donate/<donation:donation>', view_func=goods_donation_detail_view)

goods_donate_csv_view = GoodsDonateCsvView.as_view('goods_donation_download')
page.add_url_rule('/goods_donate/csv', view_func=goods_donate_csv_view, methods=['GET'])

goods_donate_check_view = GoodsDonateCheckView.as_view('goods_donation_check')
page.add_url_rule('/goods_donate/check', view_func=goods_donate_check_view, methods=['POST'])

mail_send_view = MailSendView.as_view('mail_send_view')
page.add_url_rule('/mail/send', view_func=mail_send_view, methods=["GET", "POST"])

mail_attach_view = MailAttachSend.as_view('mail_attach_view')
page.add_url_rule('/mail/attach', view_func=mail_attach_view, methods=["POST"])

nesw_list_view = BoardListView.as_view('board')
page.add_url_rule('/board/', view_func=nesw_list_view, methods=['GET'])

board_reg_view = BoardRegView.as_view('board_reg')
page.add_url_rule('/board/reg', view_func=board_reg_view)

board_edit_view = BoardEditView.as_view('board_edit')
page.add_url_rule('/board/<board:board>/edit', view_func=board_edit_view)

board_detail_view = BoardDetailView.as_view('board_view')
page.add_url_rule('/board/<board:board>', view_func=board_detail_view)

main_admin_view = MainAdminView.as_view('main_view')
page.add_url_rule('/main_admin', view_func=main_admin_view)

##########
# 구글 Oauth API 인증(Webserver Authorized)
# 2019/06/15 20:19 처리 작업 진행 중...
#############################################################################
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary',
    'https://www.googleapis.com/auth/photoslibrary.sharing'
]


@page.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(CLIENT_SECRET, scopes=GOOGLE_SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    url_for_dict = {'_external': True, '_scheme': 'https'}
    if 'test' in os.environ:
        del url_for_dict['_scheme']
    flow.redirect_uri = url_for('admin.oauth2callback', **url_for_dict)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)


@page.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_config(CLIENT_SECRET, scopes=GOOGLE_SCOPES, state=state)

    url_for_dict = {'_external': True, '_scheme': 'https'}
    if 'test' in os.environ:
        del url_for_dict['_scheme']
    flow.redirect_uri = url_for('admin.oauth2callback', **url_for_dict)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url.replace('http://', 'https://')
    if 'test' in os.environ:
        authorization_response = request.url

    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    token = GoogleToken()
    token.token_content = yaml.dump(flow.credentials)
    db_session.add(token)

    return redirect(url_for(session['success_uri']))


@page.app_context_processor
def public_context_processor():
    return {
        "roundtable_modifiable": roundtable_modifiable,
        "library2dict": library2dict,
        "library_area": lambda: area_short_name,
        "kst": datetime.timedelta(hours=9)
    }


@page.app_template_filter()
def retention(value):
    return '보유' if value else '미보유'


@page.app_template_filter()
def public(value):
    return '공개' if value else '미공개'


@page.app_template_filter()
def possible(value):
    return '협조 가능' if value else '협조 불가'


def roundtable_modifiable(round):
    current_year = datetime.datetime.now().strftime('%Y')
    entry_date = datetime.datetime(
        year=round.roundtable_date.year,
        month=round.roundtable_date.month,
        day=round.roundtable_date.day,
    )
    entry_year = entry_date.strftime('%Y')

    if current_year != entry_year:
        return False
    elif current_year == entry_year and entry_date > datetime.datetime.now():
        return True
    else:
        return False
