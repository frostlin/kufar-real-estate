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
    log_line("===START===",f"Start updating clients...")
    user_ids = get_user_ids()
    for user_id in user_ids:
        log_line("INF",f"Uptading user {user_id}")
        update_user(user_id)
    log_line("===FINISH===",f"Finished updating clients\n\n")

def update_user(user_id: int):
    search_urls = get_search_urls_for_user(user_id)

    for url in search_urls:
        log_line("INF",f"  Uptading {url.alias} --- {url.url}")

        new_estates = get_estates_for_user_notifications(user_id, url.url, ESTATE_STATUS.new)
        updated_estates = get_estates_for_user_notifications(user_id, url.url, ESTATE_STATUS.changed) 
        sold_estates = get_estates_for_user_notifications(user_id, url.url, ESTATE_STATUS.sold)
        #get_user_search_urls_for_estate()
        if sold_estates: 
            log_line("INF",f"  Sold:")
            for estate in sold_estates: log_line("INF",f"  {estate.url}")
            send_sold(user_id, sold_estates, url)
        if new_estates: 
            log_line("INF",f"  New:")
            for estate in new_estates: log_line("INF",f"  {estate.url}")
            send_new(user_id, new_estates, url)
        if updated_estates:
            log_line("INF",f"  Updated:")
            for estate in updated_estates: log_line("INF",f"  {estate.url}")
            send_updated(user_id, updated_estates, url)


def send_updated(user_id: int, estates: list[Estate], url: SearchUrl):
    #log_line("INF",f"  Sending updated")
    for estate in estates:
        try:
            send_photo(user_id, f"Цена на квартиру поменялась. {estate.price_usd_old}$ -> {estate.price_usd}$\n{repr(url)}", estate) 
            set_notification_status_idle(user_id, estate.url)
        except Exception as e: 
            send_message(user_id, f"произошла ошибка, перешлите это сообщение разработчику @Frostlin\n\nEstate: {estate.url}\n{e}\n{traceback.format_exc()}") 
            continue
    #log_line("INF",f"  Sent updated")


def send_new(user_id:int, estates: list[Estate], url: SearchUrl):
    #log_line("INF",f"  Sending new")
    for estate in estates:
        try:
            send_photo(user_id, f"Новое объявление о продаже\n{repr(url)}", estate)
            set_notification_status_idle(user_id, estate.url)
        except Exception as e: 
            send_message(user_id, f"произошла ошибка, перешлите это сообщение разработчику @Frostlin\n\nEstate: {estate.url}\n{e}\n{traceback.format_exc()}") 
            continue
    #log_line("INF",f"  Sent new")

def send_sold(user_id:int , estates: list[Estate], url: SearchUrl):
    #log_line("INF",f"  Sending sold")
    for estate in estates:
        try:
            send_photo(user_id, f"Квартира продана или объявление снято:\n {repr(url)}", estate)
            set_notification_status_archived(user_id, estate.url)
        except Exception as e: 
            send_message(user_id, f"произошла ошибка, перешлите это сообщение разработчику @Frostlin\n\nEstate: {estate.url}\n{e}\n{traceback.format_exc()}") 
            continue
    #log_line("INF",f"  Sent sold")


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
    urls = ((479073026, 'https://re.kufar.by/l/minsk/kupit/kvartiru/2k?cur=USD&prc=r%3A30000%2C51000', 'Двушки до 51к Минск'),(1232013749,'https://re.kufar.by/l/minsk/kupit/kvartiru/2k?cur=USD&prc=r%3A30000%2C51000','Двушки до 51к Минск'))
    for url in urls:
        add_search_url(int(url[0]), url[1], url[2]) 

if __name__ == "__main__":
    main()
