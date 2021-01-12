from Pixiv.pixiv import Pixiv
from Pixiv.utils.logging import *
from Pixiv.utils.path import *
import json


def get_args():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-by", "--by", type=str)

    parser.add_argument("-o", "--out", type=str, default=None)
    parser.add_argument("-id", "--illusid", type=int)
    parser.add_argument("-p", "--number_of_pages", type=int, default=1)
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-n", "--number", type=int)
    parser.add_argument('-m', "--mode", type=str, default=None)
    parser.add_argument('-l', "--limit", type=str, default='all')
    parser.add_argument("-d", "--direct_download", action="store_true")
    parser.add_argument("-ori", "--original", action='store_true')
    parser.add_argument("-a", "--author_id", type=str)
    parser.add_argument("-t", "--type", type=str, default='illustrations')

    return parser.parse_args()


def download_by_id(pixiv: Pixiv, args_):
    if args_.by != 'id':
        return

    if args_.out is None:
        out_dir = './'
    else:
        out_dir = args_.out

    if args_.number_of_pages is None:
        number_of_pages = 1
    else:
        number_of_pages = args_.number_of_pages

    pixiv.download(
        [{'illust_id': args_.illusid, 'illust_page_count': number_of_pages, 'title': 'artwork'}], out_dir,
        original=args_.original)


def download_by_searching(pixiv: Pixiv, args_):
    if args_.by != 'search':
        return

    parameters = {}

    if args_.mode == 'title':
        parameters['s_mode'] = 's_tc'
    elif args_.mode == 'perfect':
        pass
    elif args_.mode == 'partial':
        parameters['s_mode'] = 's_tag'
    elif args_.mode is None:
        parameters['s_mode'] = 's_tag'
    else:
        print_(STD_ERROR + 'parameter invalid: -m')
        return

    if args_.type not in ['manga', 'illustrations']:
        print_(STD_ERROR + 'parameter invalid: -t')
        return

    if args_.limit == 'safe':
        parameters['mode'] = 'safe'
    elif args_.limit == 'r18':
        parameters['mode'] = 'r18'
    elif args_.limit == 'all':
        pass
    else:
        print_(STD_ERROR + 'parameter error: -l')
        return

    res = pixiv.search(args_.search, args_.number, parameters=parameters, artwork_type=args_.type)

    if args_.out is None:
        out_dir = './' + args_.search
    else:
        out_dir = args_.out

    if not args_.direct_download:
        while True:
            ans = input('Sure to download? [y/n]\n')
            if ans in ['y', 'n']:
                break
        if ans == 'n':
            return

    exceptions = pixiv.download(res, out_dir, original=args_.original)

    if len(exceptions) is not 0:
        with open('exceptions_log.txt', 'w', encoding='utf-8') as f:
            for e in exceptions:
                print_exceptions_to_file(e, f)


def download_by_author(pixiv: Pixiv, args_):
    if args_.by != 'author':
        return

    if args_.type not in ['manga', 'illustrations']:
        print_(STD_ERROR + 'parameter error: -t')
        return

    res = pixiv.search_by_author(args_.author_id, args_.number, artwork_type=args_.type)

    if args_.out is None:
        path = './author_{}'.format(args_.author_id)
    else:
        path = args_.out

    if not args_.direct_download:
        while True:
            ans = input('Sure to download? [y/n]\n')
            if ans in ['y', 'n']:
                break
        if ans == 'n':
            return

    exceptions = pixiv.download(res, path, original=args_.original)
    if len(exceptions) is not 0:
        with open('exceptions_log.txt', 'w', encoding='utf-8') as f:
            for e in exceptions:
                print_exceptions_to_file(e, f)


def download_by_ranking(pixiv: Pixiv, args_):
    if args_.by != 'rank':
        return

    if args_.limit == 'r18':
        r_18 = True
    elif args_.limit == 'safe':
        r_18 = False
    elif args_.limit == 'all':
        r_18 = False
    else:
        print_(STD_ERROR + 'parameter invalid: -l')
        return

    if args_.type not in ['manga', 'illustrations']:
        print_(STD_ERROR + 'parameter invalid: -t')
        return

    if args_.mode == 'monthly':
        mode = 'monthly'
    elif args_.mode == 'weekly':
        mode = 'weekly'
    elif args_.mode == 'daily':
        mode = 'daily'
    elif args_.mode is None:
        mode = 'weekly'
    else:
        print_(STD_ERROR + 'parameter invalid: -m')
        return

    res = pixiv.search_by_ranking(args_.number, mode, args_.type, r_18)

    if args_.out is None:
        time = get_time()
        dt_string = time.strftime("%m/%d/%Y")
        dt_string = replace_system_character(dt_string, '-')
        path = './{}_top{}_artworks_{}'.format(args_.mode, args_.number, dt_string)
    else:
        path = args_.out

    if not args_.direct_download:
        while True:
            ans = input('Sure to download? [y/n]\n')
            if ans in ['y', 'n']:
                break
        if ans == 'n':
            return

    exceptions = pixiv.download(res, path, original=args_.original)
    if len(exceptions) is not 0:
        with open('exceptions_log.txt', 'w', encoding='utf-8') as f:
            for e in exceptions:
                print_exceptions_to_file(e, f)


def main():
    with open('proxy_settings.txt', 'r') as f:
        proxies = json.load(f)
    proxies = proxies if proxies['http'] is not None or proxies['https'] is not None else None
    pixiv = Pixiv('chrome', proxies=proxies)
    args = get_args()
    download_by_id(pixiv, args)
    download_by_author(pixiv, args)
    download_by_searching(pixiv, args)
    download_by_ranking(pixiv, args)


if __name__ == '__main__':
    main()


#   test field

    # headers = {
    #     'Referer': 'https://www.pixiv.net',
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
    #                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    # }
    # res = re.get(url='https://www.pixiv.net/ajax/illust/86772270', headers=headers)
    # print(res)

    # p = Pixiv()
    # p.search_by_ranking(10, 'daily', 'illustrations')

    # p = Pixiv()
    # res = p.search('arknights', 20)
    # p.download(res, './ark')
    # print(res)
    # args = get_args()
    # main(args)

    # p = Pixiv()
    # artworks, multi = p.search_by_author('5806400', 0)
    # print(artworks)
    # print(multi)

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
