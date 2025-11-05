import smtplib
import datetime
import logging
from flask import current_app
from email.mime.text import MIMEText
from flask import render_template
from .. import celery
from .models import Reminder, Post
from html.parser import HTMLParser

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logging.getLogger().setLevel(logging.DEBUG)
logs = logging.getLogger(__name__)

class HTMLFilter(HTMLParser):
    text = ""
    def handle_data(self, data):
        self.text += data


@celery.task()
def log(msg):
    return msg


@celery.task()
def multiply(x, y):
    return x * y


@celery.task(
    bind=True,
    ignore_result=True,
    default_retry_delay=300,
    max_retries=5
)
def remind(self, pk):
    
    logs.info("Remind worker %d" % pk)
    reminder = Reminder.query.get(pk)
    f = HTMLFilter()
    f.feed(reminder.text)
    msg = MIMEText(reminder.text, 'html')
    msg['Subject'] = "Your reminder"
    msg['From'] = current_app.config['SMTP_FROM']
    msg['To'] = reminder.email

    try:
        smtp_server = smtplib.SMTP(current_app.config['SMTP_SERVER'])
        smtp_server.sendmail(current_app.config['SMTP_FROM'], [reminder.email], msg.as_string())
        smtp_server.close()
        logs.info("Email sent to %s" % reminder.email)
        return
    except Exception as e:
        logs.error(e)
        self.retry(exc=e)
    

@celery.task(
    bind=True,
    ignore_result=True,
    default_retry_delay=300,
    max_retries=5
)
def digest(self):
    # find the start and end of this week
    
    year, week = datetime.datetime.now().isocalendar()[0:2]
    date = datetime.date(year, 1, 1)
    if (date.weekday() > 3):
        date = date + datetime.timedelta(7 - date.weekday())
    else:
        date = date - datetime.timedelta(date.weekday())
    delta = datetime.timedelta(days=(week - 6) * 7)
    start, end = date + delta, date + delta + datetime.timedelta(days=60)

    posts = Post.query.filter(
        Post.publish_date >= start,
        Post.publish_date <= end
    ).all()

    if (len(posts) == 0):
        return

    msg = MIMEText(render_template("digest.html", posts=posts), 'html')
    
    msg['Subject'] = "Weekly Digest"
    msg['From'] = current_app.config['SMTP_FROM']
    msg['To'] = current_app.config['SMTP_USER']
        
    try:
        smtp_server = smtplib.SMTP(current_app.config['SMTP_SERVER'])
        smtp_server.sendmail(current_app.config['SMTP_FROM'], current_app.config['SMTP_USER'], msg.as_string())
        smtp_server.close()

        return
    except Exception as e:
        self.retry(exc=e)


def on_reminder_save(mapper, connect, self):
    remind.apply_async(args=(self.id,), countdown=30)
