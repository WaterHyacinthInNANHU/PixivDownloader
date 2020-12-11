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

Open terminal under root folder of the project:

```bash
python src/pixiv.py [-h] [-s SEARCH] [-n NUMBER] [-o OUT] [--s_mode S_MODE] [--mode MODE] [-d]
```

- -s:	what you want to search for.
- -n:	number of results you want to get.
- -o:	the folder to save artworks; default by a dictionary named by the term you searched for under root folder of project.
- --s_mode:	matching option; default by partial matching; ```title``` for title matching; ```perfect``` for perfect matching.
- --mode:	age limitation; default by no limit; ```safe``` for ALL AGE; ```r18``` for R18 ONLY

- -d:	directly download searched results without asking for confirmation.

## Examples

Search for 100 artworks related to "stein gate 1000users入り".

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100
```

Search for 100 artworks related to "stein gate 1000users入り" and download them without asking for confirmation.

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100 -d
```

Search for 100 artworks perfect perfectly matched with "stein gate 1000users入り"  for all ages and save it under "./artworks".

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100 -o "./artworks" --s_mode perfect --mode safe
```

## Note

- Must have chrome installed on your device.
- Privacy concern: this tool utilize cookies of [pixiv.net](www.pixiv.net) from your chrome browser only to load [dynamic pages](https://www.doteasy.com/web-hosting-articles/what-is-a-dynamic-web-page.cfm).
- If you are using VPN or other forms of proxy, make sure you're under global mode.

