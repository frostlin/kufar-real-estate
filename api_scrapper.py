#!/usr/bin/python
import requests
import urllib.request
import os
import time
import cchardet
import base64
import json
from datetime import datetime

from object.estate import Estate
from object.search_url import SearchUrl
#webscrapper_log = open(f"{os.getcwd()}/log/webscrapper.log", "a")


def get_estates(search_url: SearchUrl, page: int):   
    
    response = requests.get(search_url.url + '&cursor=' + encode_base64('{"t":"abs","f":true,"p":' + str(page) + '}'))
    webscrapper_log.write("page " + search_url.url + "\n")
    
    products_only_filter = SoupStrainer("div", {"class": re.compile("styles_cards__(?!wrapper).*")})
    products_only = BeautifulSoup(response.text, 'lxml', parse_only=products_only_filter)
    
    products=[]
    for a in products_only.find_all("a"):
        try:
            # strip url of arguments after '?'
            href = a.get('href').split('?')[0]

            # skip some promoted bullshit kufar added that broke this scrapper
            if "account/my_ads/published" in href:
                continue
            if "promotion_services" in href:
                continue
            
            # get image from card or insert placeholder image
            image = a.find("div", {"data-testid": re.compile("segment-https.*")})
            image_href = image.get("data-testid").split('segment-')[1] if image is not None else "https://www.pngmart.com/files/22/Pepe-Sad-Download-PNG-Image.png"

            # get prices block, populate price_usd and price_byn
            prices = a.find("div", {"class": re.compile("styles_price.*")}).find_all("span")
            price_usd = int(prices[1].text.split('$')[0].replace(" ","")) if prices[0].text not in ("Договорная","Бесплатно") else 0   
            price_byn = int(prices[0].text.split('р')[0].replace(" ","")) if prices[0].text not in ("Договорная","Бесплатно") else 0
            
            parameters = a.find("div", {"class": re.compile("styles_parameters.*")}).string.split(' ')
            address = a.find("span", {"class": re.compile("styles_address.*")}).text
            room_count = int(parameters[0])
            area = float(parameters[2]) if len(parameters) > 2 else 0

            estate  = Estate(href, image_href, price_usd, price_usd, price_byn, room_count, area, address)
            estate.search_url = search_url
            products.append(estate)
        except Exception as e:
            print("ERROR on estate {}\n{}".format(href,e))
            continue
    return products


def get_response(partial_params):
    #params = {key:value for key,value in options.items() if not value}
    headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://re.kufar.by/',
            'content-type': 'application/json',
            'X-Segmentation': 'routing=web_re;platform=web;application=ad_view',
            'X-MCHack': '1',
            'Origin': 'https://re.kufar.by',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'DNT': '1',
            'Sec-GPC': '1',
    }

    params = {
            'cat': '1010',
            'cur': 'USD',
            'gtsy': 'country-belarus~province-minsk~locality-minsk',
            'lang': 'ru',
            'size': '30',
            'typ': 'sell',
    } | partial_params

    print(params)
    return requests.get('https://api.kufar.by/search-api/v1/search/rendered-paginated', params=params, headers=headers)

def get_params():
    while True:
        choice = input("""Input parameters:
        1. Condition
        2. Price range
        3. Room count
        4. Check params
        5. Get request with params
        69. Exit\n
        """)
        params = {
                "cnd": 1,
                "prc": "r:41000,45000"
                }
        if choice.isnumeric():
            choice = int(choice)
            if choice == 1:
                cnd = input("Condition (1=used, 2=new):\n")
                params |= {'cnd' : cnd}
                continue
            elif choice == 2:
                prc_low = int(input("Lower price boundary(default 0):\n") or "0")
                prc_high = int(input("Higher price boundary(default 100000000):\n") or "100000000")
                params |= {"prc" : f"r:{min(prc_low,prc_high)},{max(prc_low,prc_high)}"}
                continue
            elif choice == 3:
                room_count_params = input("Room count(whitespace separated if not one):\n")
                room_count_params = room_count_params.split()
                params |= {"rms" : f"v.or:{','.join(room_count_params)}"}
                continue
            elif choice == 4:
                print(params)
            elif choice == 5:
                r = get_response(params)
                response = r.json()
                products = response["ads"]
                total_products = response["total"]
                total_pages = total_products // 30 + 1
                print(r.url)
                print(total_pages, total_products)
                continue
            elif choice == 69:
                return


if __name__ == "__main__":
    get_params()
