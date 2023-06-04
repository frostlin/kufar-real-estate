#!/usr/bin/python
import requests 
import sys
import traceback
from env import *
from dao import *
from object.estate import Estate
from object.search_url import SearchUrl

# Define a few command handlers. These usually take the two arguments update and
# context.

def main():
    user_ids = get_user_ids()
    for user_id in user_ids:
        print(f"uptading user {user_id}")
        update_user(user_id)

def update_user(user_id: int):
    search_urls = get_search_urls_for_user(user_id)

    for url in search_urls:
        print(f"{url.alias} --- {url.url}\n")
        new_estates = get_estates_for_user_notifications(user_id, url.url, ESTATE_STATUS.new)
        print('new')
        print(*[estate.url for estate in new_estates],sep='\n')
        updated_estates = get_estates_for_user_notifications(user_id, url.url, ESTATE_STATUS.changed)
        print('updated')
        print(*[estate.url for estate in updated_estates],sep='\n')
        sold_estates = get_estates_for_user_notifications(user_id, url.url, ESTATE_STATUS.sold)
        print('sold')
        print(*[estate.url for estate in sold_estates],sep='\n')
        print()

        if sold_estates: send_sold(user_id, sold_estates, url)
        if new_estates: send_new(user_id, new_estates, url)
        if updated_estates: send_updated(user_id, updated_estates, url)


def send_updated(user_id: int, estates: list[Estate], url: SearchUrl):
    for estate in estates:
        try:
            send_photo(user_id, f"Цена на квартиру поменялась. {estate.price_usd_old}$ -> {estate.price_usd}$\n{repr(url)}", estate) 
            set_notification_status_idle(user_id, estate.url)
        except Exception as e: 
            send_message(user_id, f"произошла ошибка, перешлите это сообщение разработчику @Frostlin\n\nEstate: {estate.url}\n{e}\n{traceback.format_exc()}") 
            continue


def send_new(user_id:int, estates: list[Estate], url: SearchUrl):
    for estate in estates:
        try:
            send_photo(user_id, f"Новое объявление о продаже\n{repr(url)}", estate)
            set_notification_status_idle(user_id, estate.url)
        except Exception as e: 
            send_message(user_id, f"произошла ошибка, перешлите это сообщение разработчику @Frostlin\n\nEstate: {estate.url}\n{e}\n{traceback.format_exc()}") 
            continue

def send_sold(user_id:int , estates: list[Estate], url: SearchUrl):
    for estate in estates:
        try:
            send_photo(user_id, f"Квартира продана или объявление снято:\n {repr(url)}", estate)
            set_notification_status_archived(user_id, estate.url)
        except Exception as e: 
            send_message(user_id, f"произошла ошибка, перешлите это сообщение разработчику @Frostlin\n\nEstate: {estate.url}\n{e}\n{traceback.format_exc()}") 
            continue


def send_photo(user_id, message, estate):
    try:
        params = {
           "chat_id": str(user_id),
           "caption": message + "\n\n" + repr(estate), 
           "photo": estate.image_url,
           "parse_mode": "html"
        }
        requests.get(to_url_photo, params=params).raise_for_status()
    except Exception as e:
        print(f"Error processing {repr(estate)}")
        print(e)


def send_message(user_id, message):
    params = {
        "chat_id": str(user_id),
        "text": message,
        "parse_mode": "html"
    }
    requests.get(to_url_message, params=params).raise_for_status()




def add_search_url(user_id: int, url: str, alias: str):
    add_search_url_for_user(user_id, SearchUrl(url, alias))


def for_testing():
    urls = ((479073026, 'https://re.kufar.by/l/minsk/kupit/kvartiru/2k?blc=v.or%3A4%2C1%2C3&cnd=1&cur=USD&gbx=b%3A27.301631140136706%2C53.82325942192804%2C27.748637365722654%2C54.17400443183456&prc=r%3A30000%2C50000', 'Двушки до 50к Минск'),)
    for url in urls:
        add_search_url(int(url[0]), url[1], url[2]) 

if __name__ == "__main__":
    main()
