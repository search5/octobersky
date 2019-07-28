import paginate
from flask import request, render_template, jsonify, flash, redirect, url_for
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from social_flask_sqlalchemy.models import UserSocialAuth
from sqlalchemy import func, desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import Roundtable, SessionHost, Library, User, OTandParty


class SessionHostListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['host_name']:
            search_column = getattr(SessionHost, search_option)

        if search_option == "roundtable_num" and not search_word.isdecimal():
            flash('개최회차는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.session_host")
        if search_word:
            page_url = url_for("admin.session_host", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(SessionHost).outerjoin(Roundtable).outerjoin(Library)
        if search_word:
            if search_option == 'roundtable_num':
                records = records.filter(Roundtable.roundtable_num == search_word)
            elif search_option == 'library_name':
                records = records.filter(Library.library_name.ilike('%{}%'.format(search_word)))
            elif search_option == 'session_time':
                records = records.filter(search_column == int(search_word) - 1)
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(SessionHost.roundtable_id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/session_host.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class SessionHostRegView(MethodView):
    decorators = [is_admin_role, login_required]
    
    def get(self):
        # 새로 입력할 회차 정보를 받아와서 넘겨준다
        # 단, 지난 회차에 강연자 정보를 등록할 일이 없다고 가정한다.
        main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

        # 만약 개최회차 등록되지 않았을 경우 개최회차 등록 화면으로 돌려보낸다.
        if not main_roundtable:
            flash('진행기부를 등록하시려면 개최회차 등록부터 하셔야 합니다')
            return redirect(url_for('admin.roundtable_reg'))

        return render_template("admin/session_host_reg.html", latest_roundtable=main_roundtable)

    def post(self):
        req_json = request.get_json()

        user_record = db_session.query(User).outerjoin(UserSocialAuth).filter(
            UserSocialAuth.uid == req_json.get("hostId")).first()

        session_host_obj = SessionHost()
        session_host_obj.roundtable_id = req_json.get('roundtable_id')
        session_host_obj.library_id = req_json.get('library').get('id')
        session_host_obj.session_time = req_json.get('hostTime')
        session_host_obj.host_user_id = (user_record and user_record.id) or None
        session_host_obj.host_name = req_json.get('hostName')
        session_host_obj.host_belong = req_json.get('hostBelong')
        session_host_obj.host_hp = req_json.get('hostHp')
        session_host_obj.host_email = req_json.get('hostEmail')
        session_host_obj.host_use_yn = True

        db_session.add(session_host_obj)

        return jsonify(success=True)


class SessionHostEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, host):
        return render_template("admin/session_host_edit.html", host=host)

    def post(self, host):
        req_json = request.get_json()

        user_record = db_session.query(User).outerjoin(UserSocialAuth).filter(
            UserSocialAuth.uid == req_json.get("hostId")).first()

        host.host_num = req_json.get('hostNum')
        host.host_library_name = req_json.get('hostLibraryName')
        host.host_time = req_json.get('hostTime')
        host.host_title = req_json.get('hostTitle')
        host.host_user_id = (user_record and user_record.id) or None
        host.host_name = req_json.get('hostName')
        host.host_belong = req_json.get('hostBelong')
        host.host_hp = req_json.get('hostHp')
        host.host_email = req_json.get('hostEmail')
        host.host_use_yn = True

        db_session.add(host)

        return jsonify(success=True)


class SessionHostDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, host):
        return render_template("admin/session_host_view.html", host=host)

    def delete(self, host):
        db_session.query(OTandParty).filter(
            OTandParty.party_user_id == host.host_user_id,
            OTandParty.roundtable_id == host.roundtable_id).delete()

        db_session.delete(host)

        return jsonify(success=True)
