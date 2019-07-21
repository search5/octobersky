import paginate
import requests
from datauri import DataURI
from flask import request, url_for, render_template, jsonify, flash
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag, google_token
from nanumlectures.database import db_session
from nanumlectures.lib.google_photo import get_service, get_albums
from nanumlectures.models import PhotoAlbum, Roundtable


class PhotoListView(MethodView):
    decorators = [google_token(success_uri='admin.photo'), is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['album_name']:
            search_column = getattr(PhotoAlbum, search_option)

        if search_option == "roundtable_num" and search_word and not search_word.isdecimal():
            flash('개최회차는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.photo")
        if search_word:
            page_url = url_for("admin.photo", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(PhotoAlbum).join(Roundtable)
        if search_word:
            if search_option == 'roundtable_num':
                records = records.filter(Roundtable.roundtable_num == search_word)
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(PhotoAlbum.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/photo.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class PhotoRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        photo_service = get_service()
        photo_albums = get_albums(photo_service)

        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/photo_reg.html", photo_albums=photo_albums, roundtable=roundtable)

    def post(self):
        req_json = request.get_json()

        photo_obj = PhotoAlbum()
        photo_obj.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == req_json.get('roundtable_num')).first()
        photo_obj.album_name = req_json.get('album_name')
        photo_obj.album_link = req_json.get('album_link')
        photo_obj.album_id = req_json.get('album_id')

        tmp_req = requests.get(req_json.get('represent_img'))
        represent_img_uri = DataURI.make(tmp_req.headers['Content-Type'], None, base64=True, data=tmp_req.content)

        photo_obj.representation_image_link = str(represent_img_uri)
        photo_obj.album_description = req_json.get('description')

        db_session.add(photo_obj)

        return jsonify(success=True)


class PhotoEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, photo):
        photo_service = get_service()
        photo_albums = get_albums(photo_service)

        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/photo_edit.html", photo=photo, photo_albums=photo_albums, roundtable=roundtable)

    def post(self, photo):
        req_json = request.get_json()

        photo.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == req_json.get('roundtable_num')).first()
        photo.album_name = req_json.get('album_name')
        photo.album_link = req_json.get('album_link')
        photo.album_id = req_json.get('album_id')

        tmp_req = requests.get(req_json.get('represent_img'))
        represent_img_uri = DataURI.make(tmp_req.headers['Content-Type'], None, base64=True, data=tmp_req.content)

        photo.representation_image_link = str(represent_img_uri)
        photo.album_description = req_json.get('description')

        return jsonify(success=True)


class PhotoDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, photo):
        return render_template("admin/photo_view.html", photo=photo)

    def delete(self, photo):
        db_session.delete(photo)

        return jsonify(success=True)
