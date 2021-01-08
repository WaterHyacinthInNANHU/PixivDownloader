from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
# import re
import signal
from .utils.check_image import check_png_stream, check_jpg_jpeg_stream
from .utils.path import *
from .utils.logging import *
from .exception import *
import browser_cookie3
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from urllib import parse
from random import choice
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from time import sleep
import json


class Pixiv(object):
    domain = '.pixiv.net'
    home_page = "http://www.pixiv.net"
    ranking_page = 'https://www.pixiv.net/ranking.php'
    MAX_WORKERS = 20
    SIZE_OF_CONNECTIONS_POOL = MAX_WORKERS
    REQUEST_INTERVAL = 0.050
    SYSTEM_CHARACTERS = r'\/:*?"<>'

    def __init__(self, browser='chrome', print__=print_, proxies=None):
        """
        :param browser: 'chrome' or 'firefox'
        :param print__: a function to log information
        """
        self.headers = {
            'Referer': 'https://www.pixiv.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }
        self.print_ = print__
        self.proxies = proxies
        self.cookies = self.load_cookies(browser)

        self.session = requests.Session()
        # about pool_connections and pool_maxsize,
        # refer to: https://laike9m.com/blog/requests-secret-pool_connections-and-pool_maxsize,89/
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=Pixiv.SIZE_OF_CONNECTIONS_POOL)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.session.cookies = self.cookies
        self.session.headers = self.headers

        self.set_environment_variable()

        # set proxy for web driver
        # source: https://stackoverflow.com/questions/17082425/running-selenium-webdriver-with-a-proxy-in-python
        capabilities = None
        if proxies is not None:
            driver_proxy = Proxy()
            driver_proxy.proxy_type = ProxyType.MANUAL
            driver_proxy.http_proxy = proxies['http'] if proxies['http'] is not None else ''
            driver_proxy.ssl_proxy = proxies['https'] if proxies['https'] is not None else ''
            if browser == 'chrome':
                capabilities = webdriver.DesiredCapabilities.CHROME
            else:
                capabilities = webdriver.DesiredCapabilities.FIREFOX
            driver_proxy.add_to_capabilities(capabilities)

        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('log-level=3')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            self.web_driver = webdriver.Chrome(options=options, desired_capabilities=capabilities)
        else:
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('log-level=3')
            self.web_driver = webdriver.Firefox(options=options, desired_capabilities=capabilities)

        self.p_bar = ProgressBar()

        self._session_get_lock = Lock()

    def __del__(self):
        self.web_driver.close()

    def stop_signal_handler(self):
        self.print_("early terminate")
        self.__del__()
        exit(0)

    def check_terminate_signal(self):
        signal.signal(
            signal.SIGINT, self.stop_signal_handler()
        )
        signal.signal(
            signal.SIGTERM,
            self.stop_signal_handler()
        )

    @staticmethod
    def set_environment_variable():
        path = join_(parent_path_(root_path_()), 'driver')
        set_path_(path)

    @staticmethod
    def load_cookies_from_txt(cookie_path: str):
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
    def load_cookies(browser: str):
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

    @staticmethod
    def sort_dict_by_key(a: list, key):
        a.sort(key=lambda x: x[key])
        return a

    @staticmethod
    def merge_info_metas(names, *args: dict, essential=None):
        """
        merge info metas(dictionaries like: {'illust_id': info}) into a list likes: [{meta1}, {meta2}, ...]
        information with same id will be merged into same meta
        :param names: names of the metas
        :param args: meta dictionaries, must have the same length with [names]
        :param essential: the name of meta that result list must contents
        i.e. will remove the items without essential meta
        :return: a list of merged metas
        """
        res = []
        id_set = set()
        for arg in args:
            for item in arg:
                id_set.add(item)
        for _id in id_set:
            info = {'illust_id': _id}
            for arg, meta_name in zip(args, names):
                if _id in arg:
                    info[meta_name] = arg[_id]
            res.append(info)
        if essential is not None:
            res = [item for item in res if essential in item]
        return res

    @staticmethod
    def replace_system_character(string: str, char: str = '&'):
        rx = '[' + re.escape(Pixiv.SYSTEM_CHARACTERS) + ']'
        res = re.sub(rx, char, string)
        spaces = [1 for c in res if c == ' ']
        res = res[len(spaces):]
        return res

    @staticmethod
    def get_artworks_from_page(html: str):
        """
        get artworks's name and illusid
        :param html: page
        :return: a dictionary containing illusids and corresponding names
        """
        re_list = re.findall(r'artworks/(.*?)</a></div>', html)
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

    @staticmethod
    def get_multi_artworks_from_page(html: str):
        """
        mark artworks that contain multiple paintings
        :param html: page
        :return: a dictionary {illusid: number of paintings, }
        """
        blocks = re.findall(r'</svg></span>(.*?)</a></div>', html, re.S)
        if len(blocks) is 0:
            return {}
        multi_artworks = {}
        for block in blocks:
            illusid = re.findall(r'artworks/(.*?)\">', block)
            if len(illusid) is 0:
                continue
            number = re.findall(r'<span>(.*?)</span></div>', block)
            if len(number) is 0:
                continue
            number = number[0]
            if not number.isnumeric():
                continue
            multi_artworks[illusid[0]] = int(number)
        return multi_artworks

    @staticmethod
    def get_total_number_from_page(html):
        """
        get total number of artworks
        :param html: page
        :return: total number of artworks/None for no artwork
        """
        # block = re.findall(r'<iframe marginwidth(.*?)button type=\"submit\"', html, re.S)
        # if len(block) is 0:
        #     return None
        # print(block)
        # block = re.findall(r'<span class.*?></span></div><div class(.*?)</span><span class=', block[0], re.S)
        # # block = re.findall(r'</span></div></div><div(.*?)</span', block[0], re.S)
        # if len(block) is 0:
        #     return None
        # print(block)
        # block = re.findall(r'<span class.*?>(\d+)', block[0], re.S)
        # if len(block) is 0:
        #     return None
        # print(block)
        # return block[0]
        try:
            soup = BeautifulSoup(html, features='lxml')
            soup = soup.find('div', id='root')
            soup = soup.findChildren('div')[1]
            soup = soup.findChild('div')
            soup = soup.find_next_sibling()
            for _ in range(4):
                soup = soup.findChild('div')
            soup = soup.find_next_sibling()
            soup = soup.find_all('span')[0]
            return int(soup.text.replace(',', ''))
        except AttributeError or ValueError:  # no artwork
            return None

    def _session_get(self, url, retries=5, **kwargs):
        last_connection_exception = None
        while retries:
            try:
                self._session_get_lock.acquire()
                sleep(Pixiv.REQUEST_INTERVAL)
                self._session_get_lock.release()
                return self.session.get(url, proxies=self.proxies, **kwargs)
            except requests.exceptions.ConnectionError as e:
                last_connection_exception = e
                retries -= 1
        raise last_connection_exception

    def get_page(self, url: str, cookies=None, use_selenium: bool = False):
        """
        get page from url
        :param url: url
        :param cookies: cookies
        :param use_selenium: flag, set to use selenium to load page
        :return: a dictionary containing text of html and status code   (and response object returned by session.get)
        """
        if cookies is None:
            cookies = self.cookies
        if use_selenium:
            try:
                # reload cookies
                self.web_driver.delete_all_cookies()
                # https://stackoverflow.com/questions/41559510/selenium-chromedriver-add-cookie-invalid-domain-error/44857193
                self.web_driver.get(
                    Pixiv.home_page)
                for cookie in cookies:
                    self.web_driver.add_cookie({"name": cookie.name, "value": cookie.value, "domain": cookie.domain})
                self.web_driver.get(url)
            except Exception:
                raise PageIsNotAvailableError
            return {'html': self.web_driver.page_source, 'code': 200}
        else:
            r = self._session_get(url)
            if r.status_code is not 200:
                raise PageIsNotAvailableError
            return {'html': r.text, 'response': r, 'code': r.status_code}

    def get_url_by_illusid(self, illusid: str, number_of_paintings: int, original: bool = True):
        """
        get urls via illusid
        :param illusid: illusid
        :param number_of_paintings: number of paintings in identical illus
        :param original: flag to download original file(.png)
        :return: a list of urls of paintings
        """
        html = self.get_page('https://www.pixiv.net/ajax/illust/' + str(illusid))['html']
        urls = []
        for number in range(number_of_paintings):
            if original:
                url = re.match(r'.*\"original\":\"(.*?)\".*', html).group(1)
            else:
                url = re.match(r'.*\"regular\":\"(.*?)\".*', html).group(1)
            url = re.sub(r'p\d', 'p{}'.format(number), url)
            url = url.replace('\\', '')
            urls += [url]
        return urls

    def _download(self, illusid: str, name: str, number_of_paintings: int, path: str, original: bool):
        """
        threading download callback function
        :param illusid: illusid
        :param name: name of the artwork
        :param number_of_paintings: number of paintings in identical artwork
        :param path: path to save
        :param original: flag, set to download original picture
        :return: None
        """
        urls = self.get_url_by_illusid(illusid, number_of_paintings, original)
        if len(urls) > 1:
            path = '{}/{}_id_{}'.format(path, str(name), str(illusid))
            mkdir_(path)
        for index, url in enumerate(urls):
            try:
                response = self.get_page(url)['response']
            except PageFailedToRespond:
                self.print_('\n' + STD_ERROR + 'error occurred downloading ' + name + ' ' + url)
                continue
            bytestream = response.content
            if check_jpg_jpeg_stream(bytestream):
                image_type = '.jpg'
            elif check_png_stream(bytestream):
                image_type = '.png'
            else:
                self.print_('\n' + STD_WARNING + 'unsupported format or broken file, drop: ' + name + ' ' + url)
                continue
            if len(urls) > 1:
                p = '_p{}'.format(index)
            else:
                p = ''
            name = self.replace_system_character(name, char='%')
            file_path = '{}/{}_id_{}{}{}'.format(path, str(name), str(illusid), p, image_type)
            with open(file_path, 'wb') as f:
                f.write(bytestream)

        self.p_bar.update()

    def download(self, artworks: list, path: str, original: bool = True):
        """
        run download threads
        :param artworks: a list of artworks' information
        :param path: path to save
        :param original: flag, set to download original pictures
        :return: a list of exceptions returned by threads
        """
        if len(artworks) is 0:
            self.print_(STD_WARNING + 'no artwork to be downloaded, return')
            return

        self.print_(STD_INFO + 'start downloading ' + str(len(artworks)) + ' items...')

        self.p_bar.reset(len(artworks))
        self.p_bar.display()

        mkdir_(path)
        threads = []
        with ThreadPoolExecutor(max_workers=Pixiv.MAX_WORKERS) as executor:
            for item in artworks:
                # check multiple-painting artworks
                number_of_paintings = 1
                if 'illust_page_count' in item:
                    if int(item['illust_page_count']) is not 1:
                        number_of_paintings = int(item['illust_page_count'])
                threads.append(
                    executor.submit(self._download, item['illust_id'], item['title'], number_of_paintings, path,
                                    original))

            # handle exceptions
            exceptions = []
            for task in as_completed(threads):
                try:
                    _ = task.result()
                except Exception as _:
                    # traceback.print_exc(limit=1)
                    exceptions.append(_)
                    self.p_bar.update()
        self.print_(STD_INFO + 'download finished ')
        return exceptions

    def search(self, search_term: str, number: int, artwork_type: str = 'artworks', parameters: dict = None,
               max_retries: int = 5):
        """
        search for related artworks
        :param search_term: searched terms
        :param number: number of artworks to find
        :param artwork_type: artwork's type
        :param parameters: parameters
        :param max_retries: max times to retry while loading a page
        :return: a dictionary of artworks and a dictionary of artworks containing multiple paintings
        """
        self.print_(STD_INFO + 'start searching...')

        if number <= 0:  # download all
            self.print_(STD_INFO + 'parameter: number is 0, search for all artworks')
            number = float('inf')

        if parameters is None:
            parameters = {'s_mode': 's_tag'}

        para = str(parameters).replace('\'', '').replace('{', '').replace('}', '').replace(':', '='). \
            replace(',', '&').replace(' ', '')

        artworks = {}
        multi_artworks = {}  # a look-up dictionary, mark the artworks that have multiple paintings
        page_number = 0
        first_time_flag = True
        while True:
            retries = max_retries
            page_number += 1

            # fetch page
            url = 'https://www.pixiv.net/tags/{}/{}?{}&p={}'.format(parse.quote(search_term), artwork_type, para,
                                                                    page_number)
            self.print_(STD_INFO + 'fetching ' + url)
            while True:
                page = self.get_page(url, use_selenium=True)['html']
                new_artworks = self.get_artworks_from_page(page)
                new_multi_artworks = self.get_multi_artworks_from_page(page)

                # check for termination or retry
                if new_artworks == {}:
                    self.print_(STD_INFO + 'insufficient new artworks, retry')
                else:
                    break
                retries -= 1
                if retries == 0:
                    if first_time_flag:
                        self.print_(STD_ERROR + 'no related artworks were found, please retry or check terms you '
                                                'searched')
                        return self.merge_info_metas(['title', 'illust_page_count'], artworks, multi_artworks,
                                                     essential='title')
                    self.print_(STD_WARNING + 'insufficient new artworks, ' + str(
                        len(artworks)) + ' artworks have been collected.')
                    return self.merge_info_metas(['title', 'illust_page_count'], artworks, multi_artworks,
                                                 essential='title')

            # get max number of artworks
            # max_number = self.get_total_number_from_page(page)

            # check artworks's length, if surpassed the specific length, randomly pop items from new_artworks
            length = len(artworks)
            new_length = len(new_artworks)
            if length + new_length > number:
                for _ in range(length + new_length - number):
                    choices = choice(list(new_artworks.keys()))
                    new_artworks.pop(choices)

            # merge artworks and new_artworks, so is multi_artworks
            # if first_time_flag:
            #     if max_number is not None:
            #         self.print_(STD_INFO + str(max_number) + ' artworks were found in total.')
            self.print_(STD_INFO + str(len(new_artworks)) + ' new artworks have been collected. ')
            artworks = self.merge_two_dicts(new_artworks, artworks)
            multi_artworks = self.merge_two_dicts(new_multi_artworks, multi_artworks)
            self.print_(STD_INFO + str(len(artworks)) + ' artworks have been collected for now.')

            # check for termination
            length = len(artworks)
            if length >= number:
                break
            # if max_number is not None:
            #     if length >= max_number:
            #         break

            if first_time_flag:
                first_time_flag = False

        self.print_(STD_INFO + str(len(artworks)) + ' artworks have been collected, search completed.')
        return self.merge_info_metas(['title', 'illust_page_count'], artworks, multi_artworks,
                                     essential='title')

    def search_by_author(self, author_id: str, number: int, artwork_type: str = 'illustrations', max_retries: int = 5):
        """
        search for related artworks
        :param author_id: author id
        :param number: number of artworks to find
        :param artwork_type: artwork's type
        :param max_retries: max times to retry while loading a page
        :return: a dictionary of artworks and a dictionary of artworks containing multiple paintings
        """
        self.print_(STD_INFO + 'start searching...')

        if number <= 0:  # download all
            self.print_(STD_INFO + 'parameter: number is 0, search for all artworks')
            number = float('inf')

        assert artwork_type == 'illustrations' or 'manga'

        artworks = {}
        multi_artworks = {}  # a look-up dictionary, mark the artworks that have multiple paintings
        page_number = 0
        first_time_flag = True
        while True:
            retries = max_retries
            page_number += 1

            # fetch page
            url = 'https://www.pixiv.net/en/users/{}/{}?p={}'.format(author_id, artwork_type, page_number)
            self.print_(STD_INFO + 'fetching ' + url)
            while True:
                page = self.get_page(url, use_selenium=True)['html']
                new_artworks = self.get_artworks_from_page(page)
                new_multi_artworks = self.get_multi_artworks_from_page(page)

                # check for termination or retry
                if new_artworks == {}:
                    self.print_(STD_INFO + 'insufficient new artworks, retry')
                else:
                    break
                retries -= 1
                if retries == 0:
                    if first_time_flag:
                        self.print_(STD_ERROR + 'no related artworks were found, please retry or check terms you '
                                                'searched')
                        return self.merge_info_metas(['title', 'illust_page_count'], artworks, multi_artworks,
                                                     essential='title')
                    self.print_(STD_WARNING + 'insufficient new artworks, ' + str(
                        len(artworks)) + ' artworks have been collected.')
                    return self.merge_info_metas(['title', 'illust_page_count'], artworks, multi_artworks,
                                                 essential='title')

            # get max number of artworks
            # max_number = self.get_total_number_from_page(page)

            # check artworks's length, if surpassed the specific length, randomly pop items from new_artworks
            length = len(artworks)
            new_length = len(new_artworks)
            if length + new_length > number:
                for _ in range(length + new_length - number):
                    choices = choice(list(new_artworks.keys()))
                    new_artworks.pop(choices)

            # merge artworks and new_artworks, so is multi_artworks
            # if first_time_flag:
            #     if max_number is not None:
            #         self.print_(STD_INFO + str(max_number) + ' artworks were found in total.')
            self.print_(STD_INFO + str(len(new_artworks)) + ' new artworks have been collected. ')
            artworks = self.merge_two_dicts(new_artworks, artworks)
            multi_artworks = self.merge_two_dicts(new_multi_artworks, multi_artworks)
            self.print_(STD_INFO + str(len(artworks)) + ' artworks have been collected for now.')

            # check for termination
            length = len(artworks)
            if length >= number:
                break
            # if max_number is not None:
            #     if length >= max_number:
            #         break

            if first_time_flag:
                first_time_flag = False

        self.print_(STD_INFO + str(len(artworks)) + ' artworks have been collected, search completed.')
        return self.merge_info_metas(['title', 'illust_page_count'], artworks, multi_artworks,
                                     essential='title')

    def search_by_ranking(self, number: int, mode: str = 'daily', artwork_type: str = '', R_18: bool = False):
        if number <= 0:  # error
            self.print_(STD_ERROR + 'parameter: number is invalid')
            return []

        contents = []
        mapping = {False: '', True: '_r18'}
        r_18 = mapping[R_18]
        mapping = {'': '', 'illustrations': 'content=illust', 'manga': 'content=manga'}
        type_of_artwork = mapping[artwork_type]
        i = 0
        while True:
            i += 1
            url = 'https://www.pixiv.net/ranking.php?mode={}{}&{}&p={}&format=json'\
                .format(mode, r_18, type_of_artwork, i)
            self.print_(STD_INFO + 'fetching ' + url)
            page = self.get_page(url, use_selenium=True)['html']
            soup = BeautifulSoup(page, features='lxml')
            soup = soup.find('pre')
            js = json.loads(soup.text)
            content = js['contents']
            if content is not None:
                contents += content
                if len(contents) > number:
                    # drop tailing if surpassed
                    contents = self.sort_dict_by_key(contents, 'rank')
                    contents = contents[:number]
            else:
                if len(contents) < number:
                    self.print_(STD_WARNING + 'insufficient ranking artworks')
                break
            if len(contents) >= number:
                break
        # modify names of artworks
        for item in contents:
            item['title'] = "#{}_{}".format(item['rank'], item['title'])
        self.print_(STD_INFO + str(len(contents)) + ' artworks have been collected, search completed.')
        return contents
