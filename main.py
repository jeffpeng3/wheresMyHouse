from bs4 import BeautifulSoup
from bs4 import Tag
from urllib.parse import urlparse
from curl_cffi import get, post
from dataclasses import dataclass
from json import load, dump, loads
from os import getenv

WEBHOOK = getenv("WEBHOOK")

headers = {
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}
@dataclass
class Info:
    title: str
    url: str
    layout: str
    uid: str
    pic: str


def parseInfo(tag: Tag) -> Info:
    titleText = tag.find("a", class_="link v-middle", target="_blank")
    title = titleText["title"]
    url = titleText["href"]
    uid = urlparse(url).path

    info = tag.find("div", class_="item-info-txt")
    layout = info.find("span", class_="line").text

    pic = tag.find("img", class_="common-img")

    return Info(title=title, url=url, layout=layout, uid=uid, pic=pic["data-src"])


def sendToDiscord(info: Info):
    print(f"Sending {info.uid} to Discord")
    payload = {
        "content": None,
        "embeds": [
            {
                "title": info.title,
                "url": info.url,
                "color": None,
                "fields": [{"name": "格局", "value": info.layout}],
                "thumbnail": {
                    "url": info.pic,
                },
            }
        ],
        "attachments": [],
    }
    r = post(
        WEBHOOK,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    if r.status_code != 204:
        print(f"Error sending to Discord: {r.status_code}")


def getList(url: str) -> BeautifulSoup:
    r = get(url, impersonate="chrome", headers=headers)
    with open("list.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    return BeautifulSoup(r.text, "lxml")


with open("data.json", "r", encoding="utf-8") as f:
    seen: list[str] = load(f)


urls = loads(getenv("URLS", "[]"))

for url in urls:

    soup = getList(url)
    items = soup.find_all("div", class_="item")
    for i in filter(lambda x: x.uid not in seen, map(parseInfo, items)):
        print(i)
        sendToDiscord(i)
        seen.append(i.uid)

with open("data.json", "w", encoding="utf-8") as f:
    dump(seen, f, ensure_ascii=False, indent=4)
    print("Saved seen list")
