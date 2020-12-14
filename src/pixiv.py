from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
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
from concurrent.futures import ThreadPoolExecutor
# from tqdm import tqdm
# from concurrent.futures import as_completed
# import traceback
from time import sleep

# parameters
NUMBER_OF_WORKERS = 20
SIZE_OF_CONNECTIONS_POOL = NUMBER_OF_WORKERS
REQUEST_INTERVAL = 0.050


class Pixiv(object):
    domain = '.pixiv.net'
    home_page = "http://www.pixiv.net"
    ranking_page = 'https://www.pixiv.net/ranking.php'

    def __init__(self, browser='chrome', print__=print_):
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
        self.cookies = self.load_cookies(browser)

        self.session = requests.Session()
        # about pool_connections and pool_maxsize,
        # refer to: https://laike9m.com/blog/requests-secret-pool_connections-and-pool_maxsize,89/
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=SIZE_OF_CONNECTIONS_POOL)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
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

        self.p_bar = ProgressBar()

        self._session_get_lock = Lock()

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

    def _session_get(self, url, retries=5, **kwargs):
        last_connection_exception = None
        while retries:
            try:
                self._session_get_lock.acquire()
                sleep(REQUEST_INTERVAL)
                self._session_get_lock.release()
                return self.session.get(url, **kwargs)
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
            if index is not 0:
                p = '_p{}'.format(index)
            else:
                p = ''
            file_path = '{}/{}_id_{}{}{}'.format(path, str(name), str(illusid), p, image_type)
            with open(file_path, 'wb') as f:
                f.write(bytestream)

        self.p_bar.update()

    def download(self, artworks: dict, multi_artworks: dict, path: str, original: bool = True,
                 max_workers: int = NUMBER_OF_WORKERS):
        """
        run download threads
        :param artworks: artworks
        :param multi_artworks: a dictionary containing illusid with multiple artworks
        :param path: path to save
        :param original: flag, set to download original pictures
        :param max_workers: max workers of threading pool
        :return: None
        """
        if len(artworks) is 0:
            self.print_(STD_WARNING + 'no artwork to be downloaded, return')
            return

        self.print_(STD_INFO + 'start downloading ' + str(len(artworks)) + ' items...')

        self.p_bar.reset(len(artworks))
        self.p_bar.display()

        mkdir_(path)
        threads = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for illusid in artworks:
                # check multiple-painting artworks
                if illusid in multi_artworks:
                    number_of_paintings = int(multi_artworks[illusid])
                else:
                    number_of_paintings = 1
                threads.append(
                    executor.submit(self._download, illusid, artworks[illusid], number_of_paintings, path, original))

            # handle exceptions
            # for task in as_completed(threads):
            #     try:
            #         _ = task.result()
            #     except Exception as _:
            #         traceback.print_exc(limit=1)
        self.print_(STD_INFO + 'download finished ')

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
            multi_artworks[illusid[0]] = number[0]
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

    def search(self, search_term: str, number, artwork_type: str = 'artworks', parameters: dict = None,
               max_retries: int = 3):
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

        if number == 'ALL':  # download all
            number = float('inf')
        else:
            assert type(number) == int and number != 0
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
            url = 'https://www.pixiv.net/tags/' + parse.quote(search_term) + '/' + artwork_type + '?' + para + '&' + \
                  'p=' + str(page_number)
            self.print_(STD_INFO + 'fetching ' + url)
            while True:
                page = self.get_page(url, use_selenium=True)['html']
                new_artworks = self.get_artworks_from_page(page)
                new_multi_artworks = self.get_multi_artworks_from_page(page)

                # check for termination or retry
                if new_artworks == {}:
                    self.print_(STD_WARNING + 'insufficient new artworks, retry')
                else:
                    break
                retries -= 1
                if retries == 0:
                    if first_time_flag:
                        self.print_(STD_ERROR + 'no related artworks were found, please retry or check terms you '
                                                'searched')
                        return artworks, multi_artworks
                    self.print_(STD_WARNING + 'insufficient new artworks, ' + str(
                        len(artworks)) + ' artworks have been collected.')
                    return artworks, multi_artworks

            # get max number of artworks
            max_number = self.get_total_number_from_page(page)

            # check artworks's length, if surpassed the specific length, randomly pop items from new_artworks
            length = len(artworks)
            new_length = len(new_artworks)
            if length + new_length > number:
                for _ in range(length + new_length - number):
                    new_artworks.pop(choice(list(new_artworks.keys())))

            # merge artworks and new_artworks, so is multi_artworks
            if first_time_flag:
                if max_number is not None:
                    self.print_(STD_INFO + str(max_number) + ' artworks were found in total.')
            self.print_(STD_INFO + str(len(new_artworks)) + ' new artworks have been collected. ')
            artworks = self.merge_two_dicts(new_artworks, artworks)
            multi_artworks = self.merge_two_dicts(new_multi_artworks, multi_artworks)
            self.print_(STD_INFO + str(len(artworks)) + ' artworks have been collected for now.')

            # check for termination
            length = len(artworks)
            if length >= number:
                break
            if max_number is not None:
                if length >= max_number:
                    break

            if first_time_flag:
                first_time_flag = False

        self.print_(STD_INFO + str(len(artworks)) + ' artworks have been collected, search completed.')
        return artworks, multi_artworks


def get_args():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out", type=str, default=None)

    parser.add_argument("-id", "--illusid", type=int, default=None)
    parser.add_argument("--name", type=str, default='artwork')
    parser.add_argument("-m", "--number_of_paintings", type=int, default=1)

    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-n", "--number", type=int)

    parser.add_argument("--s_mode", type=str, default='partial')
    parser.add_argument("--mode", type=str, default='all')
    parser.add_argument("-d", "--direct_download", action="store_true")
    parser.add_argument("-ori", "--original", action='store_true')

    return parser.parse_args()


def main(args_):
    pixiv = Pixiv('chrome')

    # download by id
    if args_.illusid is not None:
        if args_.out is None:
            out_dir = './'
        else:
            out_dir = args_.out
        pixiv.download({args_.illusid: args_.name}, {args_.illusid: args_.number_of_paintings}, out_dir,
                       original=args_.original)
        return

    # search and download
    parameters = {}
    if args_.s_mode == 'title':
        parameters['s_mode'] = 's_tc'
    elif args_.s_mode == 'perfect':
        pass
    else:
        parameters['s_mode'] = 's_tag'

    if args_.mode == 'safe':
        parameters['mode'] = 'safe'
    elif args_.mode == 'r18':
        parameters['mode'] = 'r18'
    else:
        pass

    artworks, multi_artworks = pixiv.search(args_.search, args_.number, parameters=parameters)

    if not args_.direct_download:
        while True:
            ans = input('Sure to download? [y/n]\n')
            if ans in ['y', 'n']:
                break
        if ans == 'n':
            return

    if args_.out is None:
        out_dir = './' + args_.search
    else:
        out_dir = args_.out

    pixiv.download(artworks, multi_artworks, out_dir)


if __name__ == '__main__':
    args = get_args()
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

    # p = Pixiv('chrome')
    # url = 'https://www.pixiv.net/en/tags/arknights%205000users/artworks?s_mode=s_tag'
    # page = p.get_page(url, use_selenium=True)['html']
    # with open('page.html', 'w', encoding='utf-8') as f:
    #     f.write(page)
    #
    # # p = Pixiv()
    # # with open('page.html', 'r', encoding='utf-8') as f:
    # #     page = f.read()
    # # artworks = p.get_artworks_from_page(page)
    # # print(artworks)
    #
    # with open('page.html', 'r', encoding='utf-8') as f:
    #     page = f.read()
    # # artworks = Pixiv.get_multi_artworks_from_page(page)
    # # artworks = Pixiv.get_artworks_from_page(page)
    # artworks = Pixiv.get_total_number_from_page(page)
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

    # p = Pixiv()
    # url = p.get_url_by_illusid('84566199', 2, original=False)
    # print(url)

    # test of ThreadPoolExecutor
    # import time
    # from random import randrange
    # from concurrent.futures import as_completed
    #
    # def do(i, b):
    #     if get_termination():
    #         return
    #     time.sleep(randrange(1, 5)/10)
    #     # time.sleep(0.5)
    #     # print_(STD_INFO + str(i))
    #     b.update()
    #     return i
    #
    # global termination
    # lock = Lock()
    #
    # def set_termination(bo):
    #     global termination
    #     lock.acquire()
    #     termination = bo
    #     lock.release()
    #     return bo
    #
    #
    # def get_termination():
    #     global termination
    #     bo = True
    #     lock.acquire()
    #     bo = termination
    #     lock.release()
    #     return bo
    #
    #
    # artworks = [i for i in range(100)]
    # threads = []
    # # bar = tqdm(colour='green', position=0, leave=True)
    # bar = ProgressBar()
    # bar.reset(len(artworks))
    # with ThreadPoolExecutor(max_workers=3) as executor:
    #     set_termination(False)
    #     for illusid in artworks:
    #         threads.append(executor.submit(do, illusid, bar))
    #     print('\nafter assignment')
    #     bar.display()
    #     # input("terminate?")
    #     # set_termination(True)
    #     # for task in as_completed(threads):
    #     #     print_(task.result())
    #     #     pass
    # print('out_of_main')
