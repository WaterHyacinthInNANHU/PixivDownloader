# PixivDownloader
This is a scrap project to search and download artworks from pixiv.net.

Proxy settings are available.

## Install 

- [Set up python3](https://www.python.org/downloads/).

- Clone project.

- Open terminal under root folder of the project.

- Install dependencies:

```bash
pip install -r Pixiv/requirements.txt
```

- Download a [web driver](https://sites.google.com/a/chromium.org/chromedriver/downloads) according to your chrome version ([how can I get the version of my chrome browser?](https://www.businessinsider.com/what-version-of-google-chrome-do-i-have?r=DE&IR=T)) and save the it under ```driver/```.
- Log in [pixiv](www.pixiv.net) using your chrome browser with your own account for once.

## Usage

Open terminal under root folder of the project:

**Search and download**

```bash
python main.py -by search [-s SEARCH] [-n NUMBER] [-o OUT] [-m SEARCH_MODE] [-l AGE_LIMIT] [-t TYPE] [-d] [-ori] 
```

*necessary*

- -s: what you want to search for.
- -n: number of results you want to get, ```0``` for all artworks.

*optional*

- -o: the folder to save artworks; default by a dictionary named by the term you searched for under root folder of project. 
- -m: search mode; ```perfect``` for perfect matching; ```partial``` for partial matching; ```title``` for title matching;
- -l: age limitation; ```safe``` for ALL AGE; ```r18``` for R18 ONLY; ```all``` for no limit.
- -t: type of artwork; ```illustrations``` for illustrations; ```manga``` for manga.
- -d: flag, set to directly download searched results without asking for confirmation.
- -ori: flag, set to download original picture(.png), otherwise download compressed picture(.jpg).

**Download via id**

```bash
python main.py -by id [-id ILLUSID] [-o OUT] [-p PAGES] [-ori]
```

*necessary*

- -id: the id of the artwork you want to download.

*optional*

- -o: the folder to save artworks; default by root folder of project.
- -p; the number of painting contained by the target artwork; default by 1.
- -ori: flag, set to download original picture(.png); default by downloading compressed picture(.jpg).

**Download via author's id**

```bash
python main.py -by author [-aut AUTHOR_ID] [-n NUMBER] [-o OUT] [-t TYPE] [-d] [-ori]
```

*necessary*

- -aut: id of the author.
- -n: number of results you want to get, ```0``` for all artworks.

*optional*

- -o: the folder to save artworks; default by root folder of project.
- -t: type of artwork; ```illustrations``` for illustrations; ```manga``` for manga.
- -d: flag, set to directly download searched results without asking for confirmation.
- -ori: flag, set to download original picture(.png); default by downloading compressed picture(.jpg).

**Download rank**

```bash
python main.py -by rank [-n NUMBER] [-o OUT] [-m PERIOD] [-l AGE_LIMIT] [-t TYPE] [-d] [-ori] 
```

*necessary*

- -n: number of results you want to get.

*optional*

- -o: the folder to save artworks; default by a dictionary named by the term you searched for under root folder of project. 
- -m: ranking period; ```daily``` for daily rank; ```weekly``` for weekly rank; ```monthly``` for monthly rank;
- -l: age limitation; ```safe``` for ALL AGE; ```r18``` for R18 ONLY; ```all``` for no limit.
- -t: type of artwork; ```illustrations``` for illustrations; ```manga``` for manga.
- -d: flag, set to directly download searched results without asking for confirmation.
- -ori: flag, set to download original picture(.png), otherwise download compressed picture(.jpg).

## Using Proxy

If you wish to use **VPN** or other forms of proxies to access [pixiv.net](www.pixiv.net), simply modify ```proxy_settings.txt``` under the root folder.

For example, original text is written as the following.

*proxy_settings.txt*

```json
{
    "_comment":
    "please set your proxies in this file",

    "http": null,
    "https": null
}
```

Then just replace ```null``` with your proxy's address and port, which usually can be found on your proxy software.

```json
{
    "_comment":
    "please set your proxies in this file",

    "http": "http://127.0.0.1:41091",
    "https": "https://127.0.0.1:41091"
}
```

You can set proxy for **http** and **https** requests of the scrap **respectively** with different proxy's address here.

Or you can just set them as same. I used http proxy for https request as well due to ssl version problems. It's not recommended owning to safety concerns.

## Examples

**Search and download**

Search for 100 artworks related to "stein gate 1000users入り" in png format.

```bash
python main.py -by search -s "stein gate 1000users入り" -n 100 -ori
```

Search for 100 artworks related to "stein gate 1000users入り" and download them without asking for confirmation.

```bash
python main.py -by search -s "stein gate 1000users入り" -n 100 -d
```

Search for 100 artworks perfectly matched with "stein gate 1000users入り"  for all ages and save it under ```./artworks```.

```bash
python main.py -by search -s "stein gate 1000users入り" -n 100 -o "./artworks" -m perfect -l safe
```

**Download via id**

Download the artworks with id: 78396392 under ```./art```

```bash
python main.py -by id -id 78396392 -o art -p 1
```

Download the artworks with id: 82733226 under ```./art``` which contains 26 paintings.

```bash
python main.py -by id -id 82733226 -o art -p 26
```

**Download via author's id**

Download all manga of the author with id 5806400.

```bash
python main.py -by author -aut 5806400 -n 0 -t manga
```

**Download rank**

Download top 10 artworks of daily rank.

```bash
python main.py -by rank -n 10 -m daily
```

## Demo

![Capture](images/Capture.PNG)

![result](images/Capture2.PNG)

## Note

- Must have **chrome** installed on your device.
- **Privacy concern**: this tool utilize cookies of [pixiv.net](www.pixiv.net) from your chrome browser only to load [dynamic pages](https://www.doteasy.com/web-hosting-articles/what-is-a-dynamic-web-page.cfm).

