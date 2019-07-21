import csv
import datetime
from io import StringIO, BytesIO

import paginate
from flask import request, url_for, render_template, jsonify, flash, send_file
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc
from sqlalchemy.orm.attributes import flag_modified

from nanumlectures.common import is_admin_role, paginate_link_tag
from nanumlectures.database import db_session
from nanumlectures.models import DonationGoods, Roundtable
from nanumlectures.routes.public import donation_transport, donation_type


class GoodsDonateListView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        current_page = request.args.get("page", 1, type=int)
        search_option = request.args.get("search_option", '')
        search_word = request.args.get("search_word", '')

        if search_option and search_option in ['donation_description']:
            search_column = getattr(DonationGoods, search_option)

        if search_option == "roundtable_num" and search_word and not search_word.isdecimal():
            flash('개최회차는 숫자만 입력하셔야 합니다.')
            search_word = None

        page_url = url_for("admin.goods_donation")
        if search_word:
            page_url = url_for("admin.goods_donation", search_option=search_option, search_word=search_word)
            page_url = str(page_url) + "&page=$page"
        else:
            page_url = str(page_url) + "?page=$page"

        items_per_page = 10

        records = db_session.query(DonationGoods).join(Roundtable)
        if search_word:
            if search_option == 'roundtable_num':
                records = records.filter(Roundtable.roundtable_num == search_word)
            else:
                records = records.filter(search_column.ilike('%{}%'.format(search_word)))
        records = records.order_by(desc(DonationGoods.id))
        total_cnt = records.count()

        paginator = paginate.Page(records, current_page, page_url=page_url,
                                  items_per_page=items_per_page,
                                  wrapper_class=SqlalchemyOrmWrapper)

        return render_template("admin/goods_donation.html", paginator=paginator,
                               paginate_link_tag=paginate_link_tag,
                               page_url=page_url, items_per_page=items_per_page,
                               total_cnt=total_cnt, page=current_page)


class GoodsDonateRegView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/goods_donation_reg.html", roundtable=roundtable)

    def post(self):
        req_json = request.get_json()

        goods_donate = DonationGoods()
        goods_donate.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == req_json.get('roundtable_num')).first()
        goods_donate.donation_type = req_json.get('donation_type')
        goods_donate.donation_description = req_json.get('donation_description')
        goods_donate.donation_transport = req_json.get('donation_transport_type')

        db_session.add(goods_donate)

        return jsonify(success=True)


class GoodsDonateEditView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, donation):
        # 회차 정보만 모아오기(유효성 검증용)
        roundtable = map(lambda x: x[0], db_session.query(Roundtable.roundtable_num))

        return render_template("admin/goods_donation_edit.html", donation=donation, roundtable=roundtable)

    def post(self, donation):
        req_json = request.get_json()

        donation.roundtable = db_session.query(Roundtable).filter(
            Roundtable.roundtable_num == req_json.get('roundtable_num')).first()
        donation.donation_type = req_json.get('donation_type')
        donation.donation_description = req_json.get('donation_description')
        donation.donation_transport = req_json.get('donation_transport_type')

        return jsonify(success=True)


class GoodsDonateDetailView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self, donation):
        return render_template("admin/goods_donation_view.html", donation=donation)

    def delete(self, donation):
        db_session.delete(donation)

        return jsonify(success=True)


class GoodsDonateCsvView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

        records = db_session.query(DonationGoods).join(Roundtable).filter(Roundtable.id == main_roundtable.id)
        records = records.order_by(desc(DonationGoods.id))

        with StringIO() as csvfile:
            fieldnames = ['개최회차', '기부타입', '기부물품', '기부방법', '기부자']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for entry in records:
                writer.writerow({'개최회차': '{}회차'.format(entry.roundtable.roundtable_num),
                                 '기부타입': donation_type(entry.donation_type),
                                 '기부물품': entry.donation_description,
                                 '기부방법': donation_transport(entry.donation_transport),
                                 '기부자': entry.lecture_user and entry.lecture_user.name})

            mem = BytesIO()
            mem.write(csvfile.getvalue().encode('euc-kr'))
            mem.seek(0)
            csvfile.close()

            file_name = '도서기부 목록_{}.csv'.format(datetime.datetime.now().strftime("%Y-%m-%d"))

            return send_file(mem, mimetype="text/csv", as_attachment=True, attachment_filename=file_name)


class GoodsDonateCheckView(MethodView):
    decorators = [is_admin_role, login_required]

    def post(self):
        req_json = request.get_json()

        record = db_session.query(DonationGoods).filter(DonationGoods.id == int(req_json.get('donation_id'))).first()
        record.is_received = req_json.get('checked')

        return jsonify(success=True)
