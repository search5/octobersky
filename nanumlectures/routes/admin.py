import datetime

from flask import Blueprint

from nanumlectures.lib.public_context import library2dict, area_short_name
from nanumlectures.routes.admin_views.books_view import (
    BooksListView, BooksRegView, BooksEditView, BooksDetailView)
from nanumlectures.routes.admin_views.design_view import (
    DesignListView, DesignRegView, DesignEditView,
    DesignDetailView, DesignFileDownloadView)
from nanumlectures.routes.admin_views.donate_view import (
    DonateEditView, DonatePreviewView)
from nanumlectures.routes.admin_views.faq_view import (
    FaqListView, FaqRegView, FaqEditView, FaqDetailView)
from nanumlectures.routes.admin_views.host_view import (
    SessionHostRegView, SessionHostEditView,
    SessionHostDetailView, SessionHostListView)
from nanumlectures.routes.admin_views.lecture_view import (
    LectureRegView, LectureEditView, LectureDetailView,
    LectureListView, LectureFindView)
from nanumlectures.routes.admin_views.library_view import (
    LibraryRegView, LibraryEditView, LibraryDetailView,
    LibraryListView, LibrarySearchView)
from nanumlectures.routes.admin_views.member_view import (
    MemberDetailView, MemberEditView, MemberList, MemberPasswordResetView)
from nanumlectures.routes.admin_views.news_view import (
    NewsListView, NewsRegView, NewsDetailView, NewsEditView)
from nanumlectures.routes.admin_views.photo_view import (
    PhotoListView, PhotoRegView, PhotoDetailView, PhotoEditView)
from nanumlectures.routes.admin_views.roundtable_view import (
    RoundtableRegView, RoundtableDetailView,
    RoundtableEditView, RoundtableListView)

page = Blueprint('admin', __name__, url_prefix="/admin", static_folder='../static/admin', static_url_path='/static')

roundtable_list_view = RoundtableListView.as_view('main')
page.add_url_rule('/', view_func=roundtable_list_view)

roundtable_reg_view = RoundtableRegView.as_view('roundtable_reg')
page.add_url_rule('/roundtable/reg', view_func=roundtable_reg_view)

roundtable_detail_view = RoundtableDetailView.as_view('roundtable_view')
page.add_url_rule('/roundtable/<roundtable:round>', view_func=roundtable_detail_view)

roundtable_edit_view = RoundtableEditView.as_view('roundtable_edit')
page.add_url_rule('/roundtable/<roundtable:round>/edit', view_func=roundtable_edit_view)

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

donate_edit_view = DonateEditView.as_view('donate_edit')
page.add_url_rule('/donate', view_func=donate_edit_view)

donate_preview_view = DonatePreviewView.as_view('donate_preview')
page.add_url_rule('/donate/preview', view_func=donate_preview_view)


@page.app_context_processor
def public_context_processor():
    return {
        "roundtable_modifiable": roundtable_modifiable,
        "library2dict": library2dict,
        "library_area": lambda: area_short_name
    }


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
