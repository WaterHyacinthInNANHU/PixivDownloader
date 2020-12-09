from bs4 import BeautifulSoup
import requests
import re
from os.path import isfile
from utils.check_image import check_png_stream, check_jpg_jpeg_stream
from utils.logging import *
from utils.path import mkdir
from exception import *
import browser_cookie3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOption
from selenium.webdriver.firefox.options import Options as FirefoxOption
from urllib import parse
from random import choice
from concurrent.futures import ThreadPoolExecutor, as_completed

# from webdriver import Webdriver
from os.path import basename


class Pixiv():
    domain = '.pixiv.net'
    home_page = "http://www.pixiv.net"
    ranking_page = 'https://www.pixiv.net/ranking.php'

    def __init__(self, browser: str = 'chrome'):
        self.headers = {
            'Referer': 'https://www.pixiv.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }
        self.cookies = self.load_cookies(browser)
        if browser == 'chrome':
            options = ChromeOption()
            options.add_argument('--headless')
            self.web_driver = webdriver.Chrome(options=options)
        elif browser == 'firefox':
            options = FirefoxOption()
            options.add_argument('--headless')
            self.web_driver = webdriver.Firefox(options=options)

    def __del__(self):
        self.web_driver.close()

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

    def get_page(self, url: str, cookies=None, headers=None, use_selenium=False):
        if cookies is None:
            cookies = self.cookies
        if headers is None:
            headers = self.headers
        if use_selenium:
            try:
                # reload cookies
                self.web_driver.delete_all_cookies()
                self.web_driver.get(Pixiv.home_page)# https://stackoverflow.com/questions/41559510/selenium-chromedriver-add-cookie-invalid-domain-error/44857193
                for cookie in cookies:
                    self.web_driver.add_cookie({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})

                self.web_driver.get(url)
            except:
                raise PageIsNotAvailableError
            return {'html': self.web_driver.page_source,
                    'soup': BeautifulSoup(self.web_driver.page_source, features='lxml'), 'code': 200}
        else:
            r = requests.get(url, cookies=cookies, headers=headers)
            if r.status_code is not 200:
                raise PageIsNotAvailableError
            return {'html': r.text, 'response': r, 'soup': BeautifulSoup(r.text, features='lxml'),
                    'code': r.status_code}

    def get_url_by_illusid(self, illusid: int):
        html = self.get_page('https://www.pixiv.net/ajax/illust/' + str(illusid))['html']
        url = re.match(r'.*\"regular\":\"(.*?)\".*', html).group(1)
        url = url.replace('\\', '')
        return url

    def download_(self, illusid: int, name: str, path: str):
        print_(STD_INFO + 'start downloading ' + name)
        url = self.get_url_by_illusid(illusid)
        try:
            response = self.get_page(url)['response']
        except:
            print_(STD_ERROR + 'error occurred downloading ' + name + ' ' + url)
            return
        bytestream = response.content
        if check_jpg_jpeg_stream(bytestream):
            image_type = '.jpg'
        elif check_png_stream(bytestream):
            image_type = '.png'
        else:
            return
        file_path = '{}/{}{}'.format(path, str(name), image_type)
        if isfile(file_path):
            file_path = '{}/{}(id:{}){}'.format(path, str(name), str(illusid), image_type)
        with open(file_path, 'wb') as f:
            f.write(bytestream)

    def download(self, artworks: dict, path, max_workers=10):
        print_(STD_INFO + 'start downloading ' + str(len(artworks)) + ' items...')
        mkdir(path)
        threads = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for name in artworks:
                threads.append(executor.submit(self.download_, artworks[name], name, path))
            for task in as_completed(threads):
                pass
        pass

    @staticmethod
    def get_artworks_from_page(html):
        re_list = re.findall(r'.*artworks/(.*?)</a></div>.*', html)
        artworks = {}
        for string in re_list:
            string_list = string.split(r'">')
            illusid = int(string_list[0])
            name = string_list[-1]
            if name in artworks:
                name += '_'
            artworks[name] = illusid
        return artworks

    def search(self, search_term: str, number, artwork_type: str = 'artworks', parameters: dict = None):
        print_(STD_INFO + 'start searching...')
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
            # time.sleep(0.2)
            page_number += 1
            url = 'https://www.pixiv.net/tags/' + parse.quote(search_term) + '/' + artwork_type + '?' + para + '&' + \
                  'p=' + str(page_number)
            print_(STD_INFO + url)

            while True:
                page = self.get_page(url, use_selenium=True)
                section = page['soup'].find_all('section')
                if len(section) > 0:
                    break
                print_(STD_WARNING + 'cannot find specific <section> tag, load page again')

            new_artworks = self.get_artworks_from_page(page['html'])
            print_(STD_INFO + str(len(new_artworks)) + ' new artworks have been found. ')

            # check artworks's length, if surpassed the specific length, randomly pop items from the new_artworks
            length = len(artworks)
            new_length = len(new_artworks)
            if length + new_length >= number:
                if length + new_length != number:
                    print_(STD_INFO + 'surpassed by ' + str(length + new_length - number) + ' items, randomly pop.')
                    for _ in range(length + new_length - number):
                        new_artworks.pop(choice(list(new_artworks.keys())))
                    artworks = self.merge_two_dicts(new_artworks, artworks)
                break

            artworks = self.merge_two_dicts(new_artworks, artworks)

        total = len(artworks)
        print_(STD_INFO + str(total) + ' artworks have been found, return.')
        return artworks


if __name__ == '__main__':
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

    # p = Pixiv()
    # url = 'https://www.pixiv.net/tags/lappland/artworks?s_mode=s_tag'
    # page = p.get_page(url, use_selenium=True)['html']
    # with open('page.html', 'w', encoding='utf-8') as f:
    #     f.write(page)

    # p = Pixiv()
    # with open('page.html', 'r', encoding='utf-8') as f:
    #     page = f.read()
    # artworks = p.get_artworks_from_page(page)
    # print(artworks)

    p = Pixiv()
    artworks = p.search('lappland', number=50)
    p.download(artworks, '../lappland')

    # p = Pixiv()
    # cookies = p.load_cookies('chrome')
    # p.web_driver.get('https://www.pixiv.net')
    # for cookie in cookies:
    #     p.web_driver.add_cookie({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})
    #     print({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})
    # p.web_driver.get('https://www.pixiv.net/tags/lappland/artworks?s_mode=s_tag')
