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

**Search and download**

```bash
python src/pixiv.py [-o OUT] [-s SEARCH] [-n NUMBER] [--s_mode S_MODE] [--mode MODE] [-d] [-ori]
```

*necessary*

- -s: what you want to search for.
- -n: number of results you want to get.

*optional*

- -o: the folder to save artworks; default by a dictionary named by the term you searched for under root folder of project. 
- --s_mode: matching option; ```perfect``` for perfect matching; default by partial matching; ```title``` for title matching;.
- --mode: age limitation; ```safe``` for ALL AGE; ```r18``` for R18 ONLY; default by no limit.
- -d: flag, set to directly download searched results without asking for confirmation.
- -ori: flag, set to download original picture(.png), otherwise download compressed picture(.jpg).

**Download via id**

```bash
python src/pixiv.py [-o OUT] [-id ILLUSID] [--name NAME] [-m] [-ori]
```

*necessary*

- -id: the id of the artwork you want to download.

*optional*

- -o: the folder to save artworks; default by root folder of project.
- --name: a string to name the downloaded artwork; default by ```artwork```
- -m; the number of painting contained by the target artwork with identical id; default by 1.
- -ori: flag, set to download original picture(.png); default by downloading compressed picture(.jpg).

## Examples

Search for 100 artworks related to "stein gate 1000users入り" in png format.

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100 -ori
```

Search for 100 artworks related to "stein gate 1000users入り" and download them without asking for confirmation.

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100 -d
```

Search for 100 artworks perfectly matched with "stein gate 1000users入り"  for all ages and save it under ```./artworks```.

```bash
python src/pixiv.py -s "stein gate 1000users入り" -n 100 -o "./artworks" --s_mode perfect --mode safe
```

Download the artworks with id: 78396392 under ```./art```

```bash
python src/pixiv.py -id 78396392 --name artwork -o art
```

Download the artworks with id: 82733226 under ```./art``` which contains 26 paintings.

```bash
python src/pixiv.py -id 82733226 --name artwork -o art -m 26
```

## Demo

![Capture](images/Capture.PNG)

## Note

- Must have chrome installed on your device.
- Privacy concern: this tool utilize cookies of [pixiv.net](www.pixiv.net) from your chrome browser only to load [dynamic pages](https://www.doteasy.com/web-hosting-articles/what-is-a-dynamic-web-page.cfm).
- If you are using VPN or other forms of proxy, make sure you're under global mode.

