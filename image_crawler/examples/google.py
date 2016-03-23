from .. import Feeder
from .. import Parser
from .. import Crawler
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import logging
import re


class GoogleFeeder(Feeder):

    def feed(self, keyword, offset, max_num, date_min, date_max):
        base_url = 'https://www.google.com/search?'
        for i in range(offset, offset + max_num, 100):
            if date_min is not None:
                dmin = date_min.strftime('%d/%m/%Y')
            else:
                dmin = ''
            if date_max is not None:
                dmax = date_max.strftime('%d/%m/%Y')
            else:
                dmax = ''
            tbs = 'cdr:1,cd_min:{},cd_max:{}'.format(dmin, dmax)
            params = dict(q=keyword, ijn=int(i/100), start=i, tbs=tbs, tbm='isch')
            # if date_min is not None:
            #     dmin = date_min.strftime('%d/%m/%Y')
            #     if date_max is not None:
            #         dmax = date_max.strftime('%d/%m/%Y')
            #         tbs = 'cdr:1,cd_min:{},cd_max:{}'.format(dmin, dmax)
            #     else:
            #         tbs = 'cdr:1,cd_min:{}'.format(dmin)
            #     params['tbs'] = tbs
            url = base_url + urlencode(params)
            self.url_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class GoogleParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(response, 'lxml')
        image_divs = soup.find_all('div', class_='rg_di rg_el ivg-i')
        pattern = re.compile(r'imgurl=(.*?)\.jpg')
        for div in image_divs:
            href_str = div.a['href']
            match = pattern.search(href_str)
            if match:
                img_url = '{}.jpg'.format(match.group(1))
                self.task_queue.put(dict(img_url=img_url))


class GoogleImageCrawler(Crawler):

    def __init__(self, img_dir='images', log_level=logging.INFO):
        super(GoogleImageCrawler, self).__init__(
            img_dir, feeder_cls=GoogleFeeder,
            parser_cls=GoogleParser, log_level=log_level)

    def crawl(self, keyword, offset=0, max_num=1000,
              date_min=None, date_max=None, feeder_thr_num=1,
              parser_thr_num=1, downloader_thr_num=1):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error('Offset cannot exceed 1000, otherwise you '
                                  'will get duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning('Due to Google\'s limitation, you can only '
                                    'get the first 1000 result. "max_num" has '
                                    'been automatically set to %d', 1000-offset)
        else:
            pass
        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            date_min=date_min,
            date_max=date_max
        )
        downloader_kwargs = dict(max_num=max_num)
        super(GoogleImageCrawler, self).crawl(
            feeder_thr_num, parser_thr_num, downloader_thr_num,
            feeder_kwargs=feeder_kwargs,
            downloader_kwargs=downloader_kwargs)