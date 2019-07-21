from flask import render_template, request, jsonify
from flask.views import MethodView
from flask_login import login_required

from nanumlectures.common import is_admin_role
from nanumlectures.database import db_session
from nanumlectures.lib.upload import main_image_upload, s3_object_url
from nanumlectures.models import SlideCarousel


class MainAdminView(MethodView):
    decorators = [is_admin_role, login_required]

    def get(self):
        carousel = {}
        records = db_session.query(SlideCarousel)

        for entry in records:
            carousel[entry.id] = entry

        return render_template("admin/main_view.html", carousel=carousel)

    def post(self):
        # id를 key로 하여 레코드를 담아둔다.
        # 1부터 3까지 반복한다
        for i, carousel_record in enumerate(db_session.query(SlideCarousel), 1):
            carousel_record.slide_num = request.form.get('formSlideNum-{}'.format(i))

            upload_file_obj = request.files.get('formSlideImage-{}'.format(i), None)
            if upload_file_obj:
                # 첨부파일이 업로드 되었으면 기존 파일을 삭제하고 새로운 파일을 업로드하고 정보를 채워넣는다
                ret = main_image_upload(upload_file_obj, carousel_record.slide_img)
                # 사실 이건 S3 링크가 되어야 하지만 이미지 키만 등록하는 방식으로 해결함
                carousel_record.slide_img = upload_file_obj.filename
                # print("진심 여기 왜 실행함?")

            carousel_record.slide_title = request.form.get('formSlideTitle-{}'.format(i))
            carousel_record.slide_text = request.form.get('formSlideDescription-{}'.format(i))

        return jsonify(success=True)
