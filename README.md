# PixivDownloader
This is a scrap project to search and download artworks from pixiv.net

## Install

- [Set up python3](https://www.python.org/downloads/).

- Clone project.

- Open terminal under root folder of the project.

- Install dependencies:

```bash
pip install -r src/requirements.txt
```

- Download a [web driver](https://sites.google.com/a/chromium.org/chromedriver/downloads) according to your chrome version ([how can I get the version of my chrome browser?](https://www.businessinsider.com/what-version-of-google-chrome-do-i-have?r=DE&IR=T)) and replace the driver in ```src/driver/```  with your own.
- Log in [pixiv](www.pixiv.net) using your chrome browser with your own account for once.

## Usage

Under root dictionary of the project:

```bash
python src/pixiv.py [-h] [-s SEARCH] [-n NUMBER] [-o OUT] [--s_mode S_MODE] [--mode MODE]
```

- -s:	what you want to search for.
- -n:	number of results you want to get.
- -o:	the folder to save artworks; default by a dictionary named by the term you searched for under root folder of project.
- --s_mode:	match option; default by partial match; ```partial``` for partial match; ```perfect``` for perfect match
- --mode:	age limitation; default by no limit; ```safe``` for ALL AGE; ```r18``` for R18 ONLY

## Examples

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100
```

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100 -o "./artworks" --s_mode partial --mode safe
```

## Note

- Must have chrome installed on your device.
- Privacy concern: this tool utilize cookies of [pixiv.net](www.pixiv.net) from your chrome browser only to load [dynamic pages](https://www.doteasy.com/web-hosting-articles/what-is-a-dynamic-web-page.cfm).

