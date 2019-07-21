import mimetypes
import os
import smtplib
from email.header import Header
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from email.mime.text import MIMEText
from nanumlectures.settings import SES_PASS, SES_ID, SES_HOST


class SESMail:
    def __init__(self, subject, content, files):
        self.reply_addr = "october10sky@gmail.com"
        self.subject = subject
        self.content = content
        self.files = files

        self.smtp = smtplib.SMTP(SES_HOST, 587)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(SES_ID, SES_PASS)

    def send(self, to_addr, name_replace=False):
        msg = MIMEMultipart()

        msg['From'] = self.header_format('시월의하늘준비모임', self.reply_addr)

        for entry in self.files:
            ctype, encoding = mimetypes.guess_type(entry)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            with open(entry, 'rb') as fp:
                if maintype == 'image':
                    part = MIMEImage(fp.read(), _subtype=subtype)
                elif maintype == 'audio':
                    part = MIMEAudio(fp.read(), _subtype=subtype)
                else:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(fp.read())
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(entry))
                msg.attach(part)

        msg['Subject'] = Header(self.subject.format(name=to_addr["name"]), 'utf-8').encode('latin1')

        # 본문 이름 치환
        msg.attach(MIMEText(self.content.format(name=to_addr["name"]), 'html'))

        msg['To'] = self.header_format(to_addr["name"], to_addr["addr"])
        self.smtp.send_message(msg, from_addr=self.reply_addr, to_addrs=[to_addr["addr"]])

    def header_format(self, name, value):
        return "{} <{}>".format(Header(name, 'utf-8').encode('latin1'), value)
