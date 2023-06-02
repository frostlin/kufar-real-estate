#!/usr/bin/python
import requests
import urllib.request
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import re
import os
import time
import cchardet
import base64
from datetime import datetime

from object.estate import Estate
from object.search_url import SearchUrl

webscrapper_log = open(f"{os.getcwd()}/log/webscrapper.log", "a")


def get_estates(search_url: SearchUrl, page: int):   
    response = requests.get(search_url.url + '&cursor=' + encode_base64('{"t":"abs","f":true,"p":' + str(page) + '}'))
    webscrapper_log.write("page " + search_url.url + "\n")
    
    cards = SoupStrainer("div", {"class": re.compile("styles_cards__(?!wrapper).*")})
    page_only_cards = BeautifulSoup(response.text, 'lxml', parse_only=cards)
    
    products=[]
    for a in page_only_cards.find_all("a"):
        try:
            # strip url of arguments after '?'
            href = a.get('href').split('?')[0]

            # skip adverised
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



def get_page_count(url):
    print('getting page count')
    response = requests.get(url)
    page_count = BeautifulSoup(response.text, 'lxml')
    return int(page_count.find("div", {"class": re.compile("styles_listings__total.*")}).find("span").text.split(' ')[1])//30+1


def encode_base64(message):
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')   
    return base64_message

