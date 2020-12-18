from Pixiv.pixiv import Pixiv
from Pixiv.utils.logging import *


def get_args():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out", type=str, default=None)
    parser.add_argument("-id", "--illusid", type=int)
    parser.add_argument("-p", "--number_of_paintings", type=int, default=1)
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-n", "--number", type=int)
    parser.add_argument('-sm', "--search_mode", type=str, default='partial')
    parser.add_argument('-m', "--mode", type=str, default='all')
    parser.add_argument("-d", "--direct_download", action="store_true")
    parser.add_argument("-ori", "--original", action='store_true')
    parser.add_argument("-aut", "--author_id", type=str)
    parser.add_argument("-manga", "--download_manga", action='store_true')

    return parser.parse_args()


def download_by_id(pixiv: Pixiv, args_):
    if args_.illusid is None:
        return
    if args_.out is None:
        out_dir = './'
    else:
        out_dir = args_.out
    pixiv.download({args_.illusid: 'artworks'}, {args_.illusid: args_.number_of_paintings}, out_dir,
                   original=args_.original)


def search_and_download(pixiv: Pixiv, args_):
    if args_.search is None:
        return
    assert args_.number is not None
    parameters = {}
    if args_.search_mode == 'title':
        parameters['s_mode'] = 's_tc'
    elif args_.search_mode == 'perfect':
        pass
    else:
        parameters['s_mode'] = 's_tag'

    if args_.mode == 'safe':
        parameters['mode'] = 'safe'
    elif args_.mode == 'r18':
        parameters['mode'] = 'r18'
    else:
        pass

    if args_.out is None:
        out_dir = './' + args_.search
    else:
        out_dir = args_.out

    artworks, multi_artworks = pixiv.search(args_.search, args_.number, parameters=parameters)

    if not args_.direct_download:
        while True:
            ans = input('Sure to download? [y/n]\n')
            if ans in ['y', 'n']:
                break
        if ans == 'n':
            return

    exceptions = pixiv.download(artworks, multi_artworks, out_dir, original=args_.original)

    if len(exceptions) is not 0:
        # print_(STD_ERROR + 'following exceptions occurred when downloading ')
        with open('exceptions_log.txt', 'w', encoding='utf-8') as f:
            for e in exceptions:
                print_exceptions_to_file(e, f)


def download_by_author(pixiv: Pixiv, args_):
    if args_.author_id is None:
        return
    assert args_.number is not None
    if args_.download_manga:
        artworks, multi_works = pixiv.search_by_author(args_.author_id, args_.number, artwork_type='manga')
    else:
        artworks, multi_works = pixiv.search_by_author(args_.author_id, args_.number)
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

    exceptions = pixiv.download(artworks, multi_works, path, original=args_.original)
    if len(exceptions) is not 0:
        # print_(STD_ERROR + 'following exceptions occurred when downloading ')
        with open('exceptions_log.txt', 'w', encoding='utf-8') as f:
            for e in exceptions:
                print_exceptions_to_file(e, f)


def main():
    pixiv = Pixiv('chrome')
    args = get_args()
    download_by_id(pixiv, args)
    download_by_author(pixiv, args)
    search_and_download(pixiv, args)


if __name__ == '__main__':
    # main()
    args = get_args()
    print(args)
