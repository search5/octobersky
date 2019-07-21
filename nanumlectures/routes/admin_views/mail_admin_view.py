import os

import paginate
from flask import request, url_for, render_template, jsonify, flash
from flask.views import MethodView
from flask_login import login_required
from paginate_sqlalchemy import SqlalchemyOrmWrapper
from sqlalchemy import desc, func
from sqlalchemy.orm.attributes import flag_modified

from nanumlectures.common import is_admin_role, paginate_link_tag, google_token
from nanumlectures.database import db_session
from nanumlectures.lib.mail_lib import SESMail
from nanumlectures.models import PhotoAlbum, Roundtable, Library, \
    RoundtableAndLibrary, MailSend, SessionHost, Lecture


class PhotoListView(MethodView):
    """메일 전송 기록 보기용 더미 코드... TODO"""
    decorators = [is_admin_role, login_required]

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


class MailSendView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        # 최근 회차 정보 가져오기
        main_roundtable = db_session.query(Roundtable).filter(Roundtable.is_active == True).first()

        area_opened_library = db_session.query(func.distinct(Library.area)).join(
            RoundtableAndLibrary).filter(
            RoundtableAndLibrary.roundtable_id == main_roundtable.id)

        return render_template("admin/mail_send.html", area_opened_library=area_opened_library)

    def post(self):
        # 현재 표출 중인 회차의 정보를 가져온다.
        main_roundtable = db_session.query(Roundtable).filter(
            Roundtable.is_active == True).first()

        req_json = request.get_json()

        mail_record = MailSend()
        mail_record.receive_type = req_json.get('receive_type')
        # receive_type에 따라 전송할 메일 주소를 가져온다.
        # area 추가(지역별로 메일을 보낼 수도 있다)
        area = req_json.get('area')

        mail_addr = []
        if req_json.get('receive_type') == 'F':
            # 별도 메일 전송
            to_addr = {}
            if req_json.get('mail_addr').find("<") > 0:
                to_addr_split = req_json.get("mail_addr").split("<")
                to_addr["name"] = to_addr_split[0].strip()
                to_addr["addr"] = to_addr_split[1].strip("<>")
            else:
                to_addr["name"] = ""
                to_addr["addr"] = req_json.get('mail_addr')
            mail_addr = [to_addr]
        elif req_json.get('receive_type') == 'E':
            # 도서관 섭외일때
            to_addr = {}
            if req_json.get('mail_addr').find("<") > 0:
                to_addr_split = req_json.get("mail_addr").split("<")
                to_addr["name"] = to_addr_split[0].strip()
                to_addr["addr"] = to_addr_split[1].strip("<>")
            else:
                to_addr["name"] = ""
                to_addr["addr"] = req_json.get('mail_addr')
            mail_addr = [
                to_addr, {"name": "Library Team", "addr": "lib-octobersky@googlegroups.com"},
                {"name": "시월의하늘준비모임", "addr": 'october10sky@gmail.com'}]
            # mail_addr = [req_json.get("mail_addr")]
        elif req_json.get('receive_type') == 'D':
            # 진행자 일 때
            qry = SessionHost.query.filter(
                   SessionHost.roundtable_id == main_roundtable.id)

            if area == 'all':
                mail_addr = [{"name": entry.host_name, "addr": entry.host_email} for entry in qry]
            else:
                mail_addr = [{"name": entry.host_name, "addr": entry.host_email} for entry in qry
                             if entry.library.area == area]

        elif req_json.get('receive_type') == 'C':
            # 강연자 일 때
            qry = Lecture.query.filter(
                Lecture.roundtable_id == main_roundtable.id)

            if area == 'all':
                mail_addr = [{"name": entry.lecture_name, "addr": entry.lecture_email} for entry in qry]
            else:
                mail_addr = [{"name": entry.lecture_name, "addr": entry.lecture_email} for entry in qry
                             if entry.library.area == area]
        elif req_json.get('receive_type') == 'B':
            # 도서관 일 때
            libraries = RoundtableAndLibrary.query.filter(
                RoundtableAndLibrary.roundtable_id == main_roundtable.id)

            if area == 'all':
                mail_addr = [{"name": entry.library.manager_name, "addr": entry.library.manager_email} for entry in libraries]
            else:
                mail_addr = [{"name": entry.library.manager_name, "addr": entry.library.manager_email} for entry in libraries
                             if entry.library.area == area]
        elif req_json.get('receive_type') == 'A':
            # 도서관
            libraries = RoundtableAndLibrary.query.filter(
                RoundtableAndLibrary.roundtable_id == main_roundtable.id)
            mail_addr = [{"name": entry.library.manager_name, "addr": entry.library.manager_email} for entry in libraries]

            # 강연자
            mail_addr.extend([{"name": entry.lecture_name, "addr": entry.lecture_email} for entry in Lecture.query.filter(
                Lecture.roundtable_id == main_roundtable.id)])

            # 진행자
            mail_addr.extend([{"name": entry.host_name, "email": entry.host_email} for entry in SessionHost.query.filter(
                SessionHost.roundtable_id == main_roundtable.id)])

        mail_record.receive_addr = mail_addr
        mail_record.mail_subject = req_json.get('mail_subject')
        mail_record.mail_content = req_json.get('mail_content')
        mail_record.uploading_file_cnt = 0
        mail_record.uploaded_file_cnt = req_json.get('uploaded_file_cnt')
        mail_record.mail_attach = []
        mail_record.is_mail_send = False

        db_session.add(mail_record)

        # 첨부한 파일 갯수가 0인 경우는 여기서 메일을 보내고 끝낸다.
        if mail_record.uploaded_file_cnt == 0:
            # 전송 목록 필터링
            receive_addr = filter(lambda x: bool(x), mail_record.receive_addr)
            mail_record.is_mail_send = True
            mail_record.send_time = func.now()

            ses = SESMail(mail_record.mail_subject, mail_record.mail_content, mail_record.mail_attach)
            for item in receive_addr:
                name_replace = mail_record.mail_subject.find("{name}") > -1
                ses.send({"name": item["name"], "addr": item["addr"]}, name_replace)

        db_session.flush()

        return jsonify(success=True, mail_id=mail_record.id)


class MailAttachSend(MethodView):
    decorators = [is_admin_role, login_required]

    def post(self):
        upload_file_name = request.values.get("name")
        upload_file_ext = os.path.splitext(upload_file_name)

        chunk = request.values.get('chunk', 0)
        chunks = request.values.get('chunks', 0)

        chunk = int(chunk)
        chunks = int(chunks)

        temp_file_name = "/tmp/%s%s.part" % (upload_file_ext[0], upload_file_ext[1])
        dest_file_name = "/tmp/%s%s" % (upload_file_ext[0], upload_file_ext[1])

        with open(temp_file_name, "ab") as upload_file:
            req_file = request.files['file']
            upload_file.write(req_file.read())

        mail_record = MailSend.query.filter(
            MailSend.id == request.form.get('mail_id')).first()

        if chunk == (chunks - 1):
            os.rename(temp_file_name, dest_file_name)

            mail_record.uploading_file_cnt += 1
            mail_record.mail_attach.append(dest_file_name)

            flag_modified(mail_record, "mail_attach")

        send_ret = '메일 발송 결과 성공'

        if mail_record.uploading_file_cnt == mail_record.uploaded_file_cnt:
            # 전송 목록 필터링
            receive_addr = filter(lambda x: bool(x), mail_record.receive_addr)
            mail_record.is_mail_send = True
            mail_record.send_time = func.now()

            ses = SESMail(mail_record.mail_subject, mail_record.mail_content, mail_record.mail_attach)
            for item in receive_addr:
                name_replace = mail_record.mail_subject.find("{name}") > -1
                ses.send({"name": item["name"], "addr": item["addr"]}, name_replace)

        return jsonify(success=True, ret=send_ret)
