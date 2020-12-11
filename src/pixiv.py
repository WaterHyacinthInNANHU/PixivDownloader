from bs4 import BeautifulSoup
import requests
import re
import signal
from utils.check_image import check_png_stream, check_jpg_jpeg_stream
from utils.path import *
from utils.logging import *
from exception import *
import browser_cookie3
from selenium import webdriver
from urllib import parse
from random import choice
from concurrent.futures import ThreadPoolExecutor, as_completed


class Pixiv(object):
    domain = '.pixiv.net'
    home_page = "http://www.pixiv.net"
    ranking_page = 'https://www.pixiv.net/ranking.php'

    def __init__(self, browser='chrome', print__=print_):
        """
        :param browser: 'chrome' or 'firefox'
        :param version: browser version
        :param print_: a function to log information
        """
        self.headers = {
            'Referer': 'https://www.pixiv.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }
        self.print_ = print__
        self.cookies = self.load_cookies(browser)
        self.session = requests.Session()
        self.session.cookies = self.cookies
        self.session.headers = self.headers
        self.set_environment_variable()
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('log-level=3')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            self.web_driver = webdriver.Chrome(options=options)
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('log-level=3')
            self.web_driver = webdriver.Firefox(options=options)

    def __del__(self):
        self.web_driver.close()

    def stop_signal_handler(self):
        self.print_("early terminate")
        self.__del__()
        exit(0)

    @staticmethod
    def set_environment_variable():
        path = join_(parent_path_(root_path_()), 'driver')
        set_path_(path)

    def check_terminate_signal(self):
        signal.signal(
            signal.SIGINT, self.stop_signal_handler()
        )
        signal.signal(
            signal.SIGTERM,
            self.stop_signal_handler()
        )

    @staticmethod
    def load_cookies_from_txt(cookie_path):
        cookies = {}
        with open(cookie_path, 'r') as file:
            content = file.read()
            content = content.split('},')
            for item in content:
                target = item
                target = target.replace('\n', '')
                name = re.match(r'.*\"name\":\s?\"(.*?)\".*', target).group(1)
                value = re.match(r'.*\"value\":\s?\"(.*?)\".*', target).group(1)
                cookies[name] = value
        return cookies

    @staticmethod
    def load_cookies(browser):
        if browser == 'chrome':
            cookies = browser_cookie3.chrome(domain_name=Pixiv.domain)
        elif browser == 'firefox':
            cookies = browser_cookie3.firefox(domain_name=Pixiv.domain)
        else:
            raise BrowserTypeError
        return cookies

    @staticmethod
    def merge_two_dicts(x: dict, y: dict):
        """Given two dictionaries, merge them into a new dict as a shallow copy."""
        z = x.copy()
        z.update(y)
        return z

    def _session_get(self, url, retries=5, **kwargs):
        last_connection_exception = None
        while retries:
            try:
                return self.session.get(url, **kwargs)
            except requests.exceptions.ConnectionError as e:
                last_connection_exception = e
                retries -= 1
        raise last_connection_exception

    def get_page(self, url: str, cookies=None, headers=None, use_selenium=False):
        if cookies is None:
            cookies = self.cookies
        if headers is None:
            headers = self.headers
        if use_selenium:
            try:
                # reload cookies
                self.web_driver.delete_all_cookies()
                self.web_driver.get(
                    Pixiv.home_page)  # https://stackoverflow.com/questions/41559510/selenium-chromedriver-add-cookie-invalid-domain-error/44857193
                for cookie in cookies:
                    self.web_driver.add_cookie({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})

                self.web_driver.get(url)
            except:
                raise PageIsNotAvailableError
            return {'html': self.web_driver.page_source,
                    'soup': BeautifulSoup(self.web_driver.page_source, features='lxml'), 'code': 200}
        else:
            r = self._session_get(url)
            if r.status_code is not 200:
                raise PageIsNotAvailableError
            return {'html': r.text, 'response': r, 'soup': BeautifulSoup(r.text, features='lxml'),
                    'code': r.status_code}

    def get_url_by_illusid(self, illusid: int):
        html = self.get_page('https://www.pixiv.net/ajax/illust/' + str(illusid))['html']
        url = re.match(r'.*\"regular\":\"(.*?)\".*', html).group(1)
        url = url.replace('\\', '')
        return url

    def _download(self, illusid, name, path):
        self.print_(STD_INFO + 'start downloading ' + name)
        url = self.get_url_by_illusid(illusid)
        try:
            response = self.get_page(url)['response']
        except:
            self.print_(STD_ERROR + 'error occurred downloading ' + name + ' ' + url)
            return
        bytestream = response.content
        if check_jpg_jpeg_stream(bytestream):
            image_type = '.jpg'
        elif check_png_stream(bytestream):
            image_type = '.png'
        else:
            self.print_(STD_WARNING + 'unsupported format or broken file, drop: ' + name + ' ' + url)
            return
        file_path = '{}/{}_id_{}{}'.format(path, str(name), str(illusid), image_type)
        with open(file_path, 'wb') as f:
            f.write(bytestream)

    def download(self, artworks: dict, path, max_workers=10):
        self.print_(STD_INFO + 'start downloading ' + str(len(artworks)) + ' items...')
        mkdir_(path)
        threads = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for illusid in artworks:
                threads.append(executor.submit(self._download, illusid, artworks[illusid], path))
            for task in as_completed(threads):
                pass
        self.print_(STD_INFO + 'download finished ')

    @staticmethod
    def get_artworks_from_page(html):
        re_list = re.findall(r'.*artworks/(.*?)</a></div>.*', html)
        if len(re_list) == 1:
            if '<img src=' in re_list[0]:  # insufficient artworks
                return {}
        elif len(re_list) == 0:
            return {}
        artworks = {}
        for string in re_list:
            string_list = string.split(r'">')
            illusid = string_list[0]
            name = string_list[-1]
            artworks[illusid] = name
        return artworks

    def search(self, search_term: str, number, artwork_type: str = 'artworks', parameters: dict = None, retries=3):
        self.print_(STD_INFO + 'start searching...')
        if number == 'ALL':  # download all
            number = float('inf')
        else:
            assert type(number) == int and number != 0
        if parameters is None:
            parameters = {'s_mode': 's_tag'}
        para = str(parameters).replace('\'', '').replace('{', '').replace('}', '').replace(':', '='). \
            replace(',', '&').replace(' ', '')
        artworks = {}
        page_number = 0
        while True:
            page_number += 1
            url = 'https://www.pixiv.net/tags/' + parse.quote(search_term) + '/' + artwork_type + '?' + para + '&' + \
                  'p=' + str(page_number)
            self.print_(STD_INFO + 'fetching ' + url)
            while True:
                page = self.get_page(url, use_selenium=True)
                new_artworks = self.get_artworks_from_page(page['html'])
                if new_artworks == {}:
                    self.print_(STD_WARNING + 'insufficient artworks, retry')
                else:
                    break
                retries -= 1
                if retries == 0:
                    self.print_(STD_WARNING + 'insufficient artworks, ' + str(
                        len(artworks)) + ' artworks have been found, return.')
                    return artworks

            # merge artworks and new_artworks
            self.print_(STD_INFO + str(len(new_artworks)) + ' new artworks have been found. ')
            artworks = self.merge_two_dicts(new_artworks, artworks)
            self.print_(STD_INFO + str(len(artworks)) + ' artworks have been found for now.')

            # check artworks's length, if surpassed the specific length, randomly pop items from the new_artworks
            length = len(artworks)
            if length >= number:
                if length != number:
                    self.print_(STD_INFO + 'surpassed by ' + str(length - number) + ' items, randomly drop.')
                    for _ in range(length - number):
                        artworks.pop(choice(list(artworks.keys())))
                break

        self.print_(STD_INFO + str(len(artworks)) + ' artworks have been found, return.')
        return artworks


def main(args):
    pixiv = Pixiv('chrome')

    # download by id
    if args.illusid is not None:
        if args.out is None:
            out_dir = './'
        else:
            out_dir = args.out
        pixiv.download({args.illusid: args.name}, out_dir)
        return

    # search and download
    parameters = {}
    if args.s_mode == 'title':
        parameters['s_mode'] = 's_tc'
    elif args.s_mode == 'perfect':
        pass
    else:
        parameters['s_mode'] = 's_tag'

    if args.mode == 'safe':
        parameters['mode'] = 'safe'
    elif args.mode == 'r18':
        parameters['mode'] = 'r18'
    else:
        pass

    artworks = pixiv.search(args.search, args.number, parameters=parameters)

    if not args.direct_download:
        while True:
            ans = input('Sure to download? [y/n]\n')
            if ans in ['y', 'n']:
                break
        if ans == 'n':
            return

    if args.out is None:
        out_dir = './' + args.search
    else:
        out_dir = args.out

    pixiv.download(artworks, out_dir)


if __name__ == '__main__':


    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out", type=str, default=None)

    parser.add_argument("-id", "--illusid", type=int, default=None)
    parser.add_argument("--name", type=str, default='artwork')

    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-n", "--number", type=int)

    parser.add_argument("--s_mode", type=str, default='partial')
    parser.add_argument("--mode", type=str, default='all')
    parser.add_argument("-d", "--direct_download", action="store_true")

    args = parser.parse_args()

    main(args)


    # p = Pixiv()
    # url = p.get_url_by_illusid(86138069)
    # p.download(86138069, 'hhh', '.')
    # print(url)

    # p = Pixiv()
    # url = 'https://www.pixiv.net/tags/lappland/artworks?s_mode=s_tag'
    # r = requests.get(url, cookies=p.cookies, headers=p.headers)
    # with open('page.html', 'w', encoding='utf-8') as f:
    #     f.write(r.text)

    # p = Pixiv()
    # url = p.get_url_by_illusid(86138069)

    # p = Pixiv('chrome', 87)
    # url = 'https://www.pixiv.net/tags/%E3%82%A2%E3%83%BC%E3%82%AF%E3%83%8A%E3%82%A4%E3%83%8410000users%E5%85%A5%E3%82%8A/artworks?mode=safe&p=8&s_mode=s_tag'
    # page = p.get_page(url, use_selenium=True)['html']
    # with open('page.html', 'w', encoding='utf-8') as f:
    #     f.write(page)
    #
    # p = Pixiv()
    # with open('page.html', 'r', encoding='utf-8') as f:
    #     page = f.read()
    # artworks = p.get_artworks_from_page(page)
    # print(artworks)

    # p = Pixiv('chrome')
    # terms = ['stein gate 1000users入り']
    # # terms = ['アークナイツ10000users入り']
    # # terms = ['lappland 10000users入り']
    # for t in terms:
    #     artworks = p.search(t, number=200)
    #     # p.download(artworks, '../' + t)


    # p = Pixiv()
    # cookies = p.load_cookies('chrome')
    # p.web_driver.get('https://www.pixiv.net')
    # for cookie in cookies:
    #     p.web_driver.add_cookie({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})
    #     print({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})
    # p.web_driver.get('https://www.pixiv.net/tags/lappland/artworks?s_mode=s_tag')

    # from utils.path import *
    # path = join_(parent_path_(root_path_()), 'chromedrivers', '87', 'chromedirver.exe')
    # print(path)
    # path = ';{}'.format(path)
    # os.environ['PATH'] += path
    # env = os.environ['PATH']
    # print(path)
    # print(env)