import uuid
from io import BytesIO

import paginate
from flask import request, url_for, render_template, jsonify, send_file, flash
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.lib.upload import upload_blob, download_blob, delete_blob
from nanumlectures.models import DesignData, Roundtable


class DesignListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['design_name']:
            search_column = getattr(DesignData, search_option)

        if search_option == "roundtable_num" and search_word and not search_word.isdecimal():
            flash('개최회차는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.design")
        if search_word:
            page_url = url_for("admin.design", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(DesignData).join(Roundtable)
        if search_word:
            if search_option == 'roundtable_num':
                records = records.filter(Roundtable.roundtable_num == search_word)
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(DesignData.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/design.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class DesignRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/design_reg.html", roundtable=roundtable)

    def post(self):
        new_filename = str(uuid.uuid4())

        design_obj = DesignData()
        design_obj.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == request.form.get('roundtable_num')).first()
        design_obj.design_name = request.form.get('design_name')
        design_obj.design_files = {request.files['img'].filename: new_filename}
        design_obj.design_description = request.form.get('description')

        db_session.add(design_obj)

        upload_blob(request.files['img'], new_filename, request.files['img'].mimetype)

        return jsonify(success=True)


class DesignEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, design):
        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/design_edit.html", design=design, roundtable=roundtable)

    def post(self, design):
        design.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == request.form.get('roundtable_num')).first()
        design.design_name = request.form.get('design_name')

        if request.files.get('img', None):
            delete_blob(tuple(design.design_files.values())[0])

            new_filename = str(uuid.uuid4())
            design.design_files = {request.files['img'].filename: new_filename}

            upload_blob(request.files['img'], new_filename, request.files['img'].mimetype)

        design.design_description = request.form.get('description')

        return jsonify(success=True)


class DesignDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, design):
        return render_template("admin/design_view.html", design=design)

    def delete(self, design):
        delete_blob(tuple(design.design_files.values())[0])

        db_session.delete(design)

        return jsonify(success=True)


class DesignFileDownloadView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, design, filename):
        download_file = BytesIO()
        download_blob(design.design_files[filename], download_file)
        download_file.seek(0)

        return send_file(
            download_file,
            as_attachment=True,
            attachment_filename=filename)
