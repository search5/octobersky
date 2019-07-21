import paginate
from flask import render_template, jsonify, request, url_for
from flask.views import MethodView
from flask_login import login_required, current_user
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag, is_library_owner_role
from nanumlectures.database import db_session
from nanumlectures.models import Library


class LibraryListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')
        area = request.args.get("area", 'all')

        if search_option and search_option in ['library_name', 'library_addr']:
            search_column = getattr(Library, search_option)

        page_url = url_for("admin.library_list")
        if search_word:
            page_url = url_for("admin.library_list", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(Library)
        if search_word:
            records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        if area != "all":
            records = records.filter(Library.area == area)
        records = records.order_by(desc(Library.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/library.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class LibraryRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        return render_template("admin/library_reg.html")

    def post(self):
        req_json = request.get_json()

        library_obj = Library()
        library_obj.library_name = req_json.get('libraryName')
        library_obj.library_addr = req_json.get('libraryAddr')
        library_obj.manager_name = req_json.get('managerName')
        library_obj.manager_email = req_json.get('managerEmail')
        library_obj.manager_description = req_json.get('managerDescription')
        library_obj.library_place = req_json.get('libraryPlace')
        library_obj.place_seats = req_json.get('placeSeats')
        library_obj.pr_production = req_json.get('prProduction')
        library_obj.projector_screen = bool(req_json.get('projector_screen'))
        library_obj.projector_notebook = bool(req_json.get('projector_notebook'))
        library_obj.sound_equipment = bool(req_json.get('sound_equipment'))
        library_obj.camcorder_yn = bool(req_json.get('camcorder_yn'))
        library_obj.lecture_video_recording_yn = bool(req_json.get('lecture_video_recording_yn'))
        library_obj.coordinate_photography_yn = bool(req_json.get('coordinate_photography_yn'))
        library_obj.internet_yn = bool(req_json.get('internet_yn'))
        library_obj.etc_equipment = req_json.get('etc_equipment')
        library_obj.manager_hp = req_json.get('managerHp')
        library_obj.library_tel = req_json.get('libraryTel')
        library_obj.library_fax = req_json.get('libraryFax')
        library_obj.library_homepage = req_json.get('libraryHomepage')
        library_obj.library_description = req_json.get('libraryDescription')
        library_obj.expected_audience = req_json.get('expectedAudience')
        library_obj.expected_listens = req_json.get('expectedListens')
        library_obj.lat = req_json.get('libraryLat')
        library_obj.long = req_json.get('libraryLong')
        if req_json.get('libraryAddr').split(" ")[0] == '제주특별자치도':
            library_obj.area = '제주도'
        elif req_json.get('libraryAddr').split(" ")[0] == '세종특별자치시':
            library_obj.area = '세종시'
        else:
            library_obj.area = req_json.get('libraryAddr').split(" ")[0]

        db_session.add(library_obj)

        return jsonify(success=True)


class LibraryEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, library):
        return render_template("admin/library_edit.html", library=library)

    def post(self, library):
        req_json = request.get_json()

        library.library_addr = req_json.get('libraryAddr')
        library.manager_name = req_json.get('managerName')
        library.manager_hp = req_json.get('managerHp')
        library.manager_email = req_json.get('managerEmail')
        library.manager_description = req_json.get('managerDescription')
        library.library_place = req_json.get('libraryPlace')
        library.place_seats = req_json.get('placeSeats')
        library.pr_production = req_json.get('prProduction')
        library.projector_screen = bool(req_json.get('projector_screen'))
        library.projector_notebook = bool(req_json.get('projector_notebook'))
        library.sound_equipment = bool(req_json.get('sound_equipment'))
        library.camcorder_yn = bool(req_json.get('camcorder_yn'))
        library.lecture_video_recording_yn = bool(req_json.get('lecture_video_recording_yn'))
        library.coordinate_photography_yn = bool(req_json.get('coordinate_photography_yn'))
        library.internet_yn = bool(req_json.get('internet_yn'))
        library.etc_equipment = req_json.get('etc_equipment')
        library.library_tel = req_json.get('libraryTel')
        library.library_fax = req_json.get('libraryFax')
        library.library_homepage = req_json.get('libraryHomepage')
        library.library_description = req_json.get('libraryDescription')
        library.expected_audience = req_json.get('expectedAudience')
        library.expected_listens = req_json.get('expectedListens')
        library.lat = req_json.get('libraryLat')
        library.long = req_json.get('libraryLong')
        if req_json.get('libraryAddr').split(" ")[0] == '제주특별자치도':
            library.area = '제주도'
        elif req_json.get('libraryAddr').split(" ")[0] == '세종특별자치시':
            library.area = '세종시'
        else:
            library.area = req_json.get('libraryAddr').split(" ")[0]

        return jsonify(success=True)


class LibraryDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, library):
        return render_template("admin/library_view.html", library=library)


class LibrarySearchView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        library_name = request.args.get('library_name', '')

        records = []

        if library_name:
            find_records = db_session.query(Library).filter(
                Library.library_name.ilike(
                    '%{0}%'.format(library_name))).order_by(
                desc(Library.id))
            for library_rec in find_records:
                records.append(dict(
                    id=library_rec.id,
                    library_name=library_rec.library_name,
                    library_addr=library_rec.library_addr
                ))

        return jsonify(success=True, items=records)


class LibraryOwnerView(MethodView):
    decorators = [is_library_owner_role, login_required]

    def get(self):
        # 로그인한 유저가 어떤 도서관의 담당자인지 식별해야 한다
        return render_template("admin/library_owner.html", library=current_user.library)

    def post(self):
        req_json = request.get_json()

        library = current_user.library
        library.library_name = req_json.get('libraryName')
        library.library_addr = req_json.get('libraryAddr')
        library.manager_name = req_json.get('managerName')
        library.manager_hp = req_json.get('managerHp')
        library.manager_email = req_json.get('managerEmail')
        library.manager_description = req_json.get('managerDescription')
        library.library_place = req_json.get('libraryPlace')
        library.place_seats = req_json.get('placeSeats')
        library.pr_production = req_json.get('prProduction')
        library.projector_screen = bool(req_json.get('projector_screen'))
        library.projector_notebook = bool(req_json.get('projector_notebook'))
        library.sound_equipment = bool(req_json.get('sound_equipment'))
        library.camcorder_yn = bool(req_json.get('camcorder_yn'))
        library.lecture_video_recording_yn = bool(req_json.get('lecture_video_recording_yn'))
        library.coordinate_photography_yn = bool(req_json.get('coordinate_photography_yn'))
        library.internet_yn = bool(req_json.get('internet_yn'))
        library.etc_equipment = req_json.get('etc_equipment')
        library.library_tel = req_json.get('libraryTel')
        library.library_fax = req_json.get('libraryFax')
        library.library_homepage = req_json.get('libraryHomepage')
        library.library_description = req_json.get('libraryDescription')
        library.expected_audience = req_json.get('expectedAudience')
        library.expected_listens = req_json.get('expectedListens')
        library.lat = req_json.get('libraryLat')
        library.long = req_json.get('libraryLong')
        if req_json.get('libraryAddr').split(" ")[0] == '제주특별자치도':
            library.area = '제주도'
        elif req_json.get('libraryAddr').split(" ")[0] == '세종특별자치시':
            library.area = '세종시'
        else:
            library.area = req_json.get('libraryAddr').split(" ")[0]

        return jsonify(success=True)
