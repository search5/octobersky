# 10월의 하늘
## 공개 목적

10월의 하늘은 과학을 사랑하고 아끼는 모든 이의 축제로 이 취지에 맞게 10월의 하늘 홈페이지 코드 전체를 공개합니다.

## 설치 사양

- Python 3.7(Python 3.5+)
- PostgreSQL 9+
- Windows, OSX, Linux

## 설치 방법

```bash
$ git clone https://github.com/search5/octobersky.git
$ python3 -m venv venv
$ source venv/bin/activate (Not Windows)
$ venv\Scripts\activate (Only Windows)
$ cd octobersky
$ pip install -r requirements.txt
$ python manage.py syncdb
$ python manage.py run
```

## DB 계정 생성

사용자가 자율적으로 생성하여 nanumlectures/database.py 파일을 수정해주시면 됩니다. DB 설정은 여러분이 알아서...
설치과정에서 database.py 파일을 수정하고 난 뒤에 반드시 syncdb를 실행하셔야 합니다.

## 소셜 연동

10월의 하늘은 소셜 연동 기준하여 구글, 페이스북, 카카오, 네이버가 연동 대상이며 nanumlectures/settings.py 파일에 해당 내용을 기록하시면 됩니다.

**감사합니다**

