#!/usr/bin/env python
import glob
import os
import re
import zipfile
from functools import partial

import click
import shlex
import platform

import yaml
from flask.cli import FlaskGroup
from sqlalchemy import asc

from nanumlectures import main
from subprocess import Popen, PIPE

from nanumlectures.database import db_session
from nanumlectures.models import Library, PageTemplate


def create_app():
    return main.app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Management script for the Wiki application."""


@cli.command()
def syncdb():
    """데이터베이스 초기화 작업"""

    from nanumlectures.database import init_db
    init_db()

    click.echo(click.style("데이터베이스 생성이 완료되었습니다.", fg='blue'))


@cli.command()
def dropdb():
    """데이터베이스 지우기"""

    from nanumlectures.database import drop_db
    drop_db()

    click.echo(click.style("데이터베이스의 내용이 전부 지워졌습니다.", fg='red'))


def version_up(version, update_item):
    next_item = dict(patch='minor', minor='major')

    if version[update_item] < 100:
        version[update_item] += 1
    else:
        version[update_item] = 0
        if update_item != 'major':
            return version
        version_up(version, next_item[update_item])

    return version


@cli.command()
def export_aws():
    """아마존으로 쉽게 내보낼 수 있도록 zip 파일 생성"""
    # 생성할 압축 파일명 지정
    version_file = open("export_aws_version.yml")
    version_info = yaml.load(version_file)
    new_version = version_up(version_info, 'patch')

    new_zip_file = 'octobersky-v{major}.{minor}.{patch}.zip'.format(**dict(new_version))

    aws_export_file_re = re.compile('octobersky-v([0-9]+)\.([0-9]+)\.([0-9]+)\.zip')

    octobersky_export_zip = zipfile.ZipFile(new_zip_file, 'w')

    for root, folders, files in os.walk("."):
        for entry in files:
            full_path = os.path.join(root, entry)

            if ".git/" in full_path:
                continue
            elif ".idea/" in full_path:
                continue
            elif "__pycache__/" in full_path:
                continue
            elif ".gitignore" in full_path:
                continue
            elif ".elasticbeanstalk" in full_path:
                continue
            elif aws_export_file_re.match(entry):
                continue

            octobersky_export_zip.write(full_path, full_path, compress_type=zipfile.ZIP_DEFLATED)

    octobersky_export_zip.close()

    yaml.dump(new_version, open("export_aws_version.yml", "w"), default_flow_style=False)

    click.echo("아마존으로 내보낼 파일명: {}".format(new_zip_file))


@cli.command(name="calc_line")
def calc_line():
    import os
    import stat

    wc = 0
    size = 0

    def file_wc(path):
        with open(path, 'rb') as file_obj:
            return len(file_obj.readlines())

    def file_size(path):
        return os.stat(path)[stat.ST_SIZE]

    for root, dirs, files in os.walk("."):
        for entry in files:
            last_path = os.path.join(root, entry)
            if 'nanumlectures' in last_path:
                if 'nanumlectures/static' in last_path:
                    continue
                elif 'nanumlectures/templates/admin_templates' in last_path:
                    continue
                elif 'nanumlectures/templates/public_templates' in last_path:
                    continue

                wc += file_wc(last_path)
                size += file_size(last_path)
            elif 'migration' in last_path:
                continue

    wc += len(open('.gitignore', 'r').readlines())
    wc += len(open('manage.py', 'r').readlines())

    click.echo('현재까지 {0:#,} 줄을 작성하셨습니다. 분발하셔야 하겠어요'.format(wc))
    click.echo('현재까지 {0:#,} 용량을 작성하셨습니다. 분발하셔야 하겠어요'.format(size))


process_complete_lib = {}
all_id = []


def library_check(library_name, entry):
    return (entry['place_name'] == library_name) and (entry['category_name'].endswith('도서관'))


@cli.command()
def library_update():
    lib_addrs = glob.glob("t/*.yml")

    for entry in lib_addrs:
        file = yaml.load(open(entry))
        # 반복중인 도서관 이름과 yml 파일에서 가져온 이름이 같을 때까지 lib_iter를 반복한다.
        db_record = db_session.query(Library).filter(Library.id == int(file['id'])).first()

        db_record.library_addr = file['addr']
        db_record.lat = file['lat']
        db_record.long = file['long']
        db_record.area = file['addr'].split(" ")[0]
        # print(file)

    db_session.commit()
    click.echo("DB에 모든 정보가 업데이트 되었습니다")


@cli.command()
def tmpl_update():
    record = PageTemplate()
    record.page_name = 'public/boost.html'
    record.page_content = open('nanumlectures/templates/public/boost2.html', 'r').read()

    db_session.add(record)
    db_session.commit()

    click.echo("DB에 후원 정보 페이지가 입력 되었습니다")


if __name__ == '__main__':
    cli.main()
