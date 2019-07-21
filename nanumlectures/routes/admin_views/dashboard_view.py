from flask import render_template
from flask.views import MethodView
from flask_login import login_required
from sqlalchemy import func

from nanumlectures.common import is_admin_role
from nanumlectures.database import db_session
from nanumlectures.models import Library, Roundtable, RoundtableAndLibrary


class DashboardView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        # 메인 강연 회차를 가져온다.
        main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

        area_opened_library = db_session.query(func.distinct(Library.area)).join(
            RoundtableAndLibrary).filter(
            RoundtableAndLibrary.roundtable_id == main_roundtable.id)
        opened_area = [entry[0] for entry in area_opened_library]

        # 강연이 열리는 도서관 목록을 가져온다.
        opened_library = RoundtableAndLibrary.query.filter(RoundtableAndLibrary.roundtable == main_roundtable)

        records = []

        for library_match in opened_library:
            # 도서관별 토탈 강연 회차를 가져와서 도서관에 매치된 강연 회차가 몇개 존재하는지 가지고 온다.
            records.append(dict(
                area=library_match.library.area,
                library_id=library_match.library.id,
                library_name=library_match.library.library_name,
                round_num=library_match.round_num,
                lecture_cnt=len(library_match.library.lecture),
                host_cnt=len(library_match.library.host)
            ))

        return render_template("admin/dashboard.html", opened_area=opened_area, opened_library=records)
