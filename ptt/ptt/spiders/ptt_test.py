"""
https://city.shaform.com/zh/2016/02/28/scrapy/
"""
import scrapy
import logging
from scrapy.http import FormRequest
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import configparser
import json
import os

config = configparser.ConfigParser()
config.read("scrapy.cfg")


class PTTSpider(scrapy.Spider):
    name = 'ptt'
    allowed_domains = ['ptt.cc']
    start_urls = ('https://www.ptt.cc/bbs/MuscleBeach/index.html',)

    # self parameter
    _retries = 0
    MAX_RETRY = 1

    def parse(self, response):
        if len(response.xpath('//div[@class="over18-notice"]')) > 0:
            if self._retries < PTTSpider.MAX_RETRY:
                self._retries += 1
                logging.warning('retry {} times...'.format(self._retries))
                yield FormRequest.from_response(response,
                                                formdata={'yes': 'yes'},
                                                callback=self.parse)
            else:
                logging.warning('you cannot pass')
        else:
            urls_list = load_url_history()
            for item in response.css('.r-ent > div.title'):
                try:
                    href = item.css('a::attr(href)').extract()[0]
                    url = response.urljoin(href)
                    if url not in urls_list:
                        title = item.css('::text').extract()[1]
                        if config['keys']['want'] in title and config['keys']['no_want'] not in title:
                            send(title + "\n" + url)
                            urls_list.append(url)
                            save_url(urls_list)
                except:
                    pass


"""
https://blog.taiker.space/python-how-to-send-an-email-with-python/
"""


def send(body):
    account = config['email']['account']
    password = config['email']['password']
    msg = MIMEMultipart()
    msg['From'] = account
    msg['To'] = account
    msg['Subject'] = "PTT TOOL MAN"

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(account, password)
    text = msg.as_string()
    server.sendmail(msg['From'], msg['To'], text)
    server.quit()


history_name = 'url_history'


def load_url_history():
    if os.path.exists(history_name):
        with open(history_name) as json_file:
            urls = json.load(json_file)
        return urls
    return []


def save_url(urls):
    with open(history_name, 'w') as outfile:
        json.dump(urls[-16:], outfile)
