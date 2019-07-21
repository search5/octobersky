import paginate
from flask import render_template, jsonify, request, url_for
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from social_flask_sqlalchemy.models import UserSocialAuth
from sqlalchemy import desc

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import Library, User


class MemberList(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['name', 'email', 'phone']:
            search_column = getattr(User, search_option)

        page_url = url_for("admin.member_list")
        if search_word:
            page_url = url_for("admin.member_list", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(User)
        if search_word:
            if search_option == "phone":
                records = records.filter(User.phone_search.ilike('%{}%'.format(search_word.replace("-", ""))))
            elif search_option == "username":
                # 다른데서 먼저 찾아야 한다.
                social_auth_records = db_session.query(UserSocialAuth.user_id).filter(
                    UserSocialAuth.provider == 'username', UserSocialAuth.uid.ilike('%{}%'.format(search_word)))
                records = records.filter(User.id.in_(social_auth_records))
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(User.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/member.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class MemberDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, uid):
        return render_template("admin/member_view.html", record=uid)

    def delete(self, uid):
        social_auth_record = db_session.query(UserSocialAuth).filter(UserSocialAuth.user_id == uid.id).first()
        db_session.delete(social_auth_record)
        db_session.delete(uid)

        return jsonify(success=True)


class MemberEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, uid):
        return render_template("admin/member_modify.html", record=uid)

    def post(self, uid):
        req_json = request.get_json()

        if len(req_json.get('password', '')) > 0:
            uid.set_password(req_json.get('password'))
        uid.name = req_json.get('name')
        uid.email = req_json.get('email')
        uid.phone = req_json.get('phone')
        uid.usertype = req_json.get('usertype')

        if 'id' in req_json.get('library'):
            # 이 때 기존에 지정된 도서관 담당자가 있는 경우 일반 유저로 돌려놔야 한다.
            lib_rec = db_session.query(Library).filter(Library.id == req_json.get('library').get('id')).first()
            if bool(lib_rec.manager_id):
                other_library_manager = User.query.filter(User.id == lib_rec.manager_id).first()
                other_library_manager.usertype = 'C'
            uid.library = lib_rec

        return jsonify(success=True)


class MemberPasswordResetView(MethodView):
    decorators = [is_admin_role, login_required]

    def post(self, uid):
        uid.set_password('1234')

        return jsonify(success=True)
