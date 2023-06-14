#!/usr/bin/python
import psycopg2
import sys
import os
from psycopg2.extensions import AsIs
import time
from datetime import datetime
from collections import namedtuple
import traceback

from dbenv import *
from object.estate import Estate
from object.search_url import SearchUrl

#
# DIRE NEED FOR REFACTORING
#

sql_log = open(f"{os.getcwd()}/log/database.log", "a")
connection = psycopg2.connect(host=postgres_address, port=port, user=postgres_user, password=postgres_user_password, dbname=db_name_dev)
ESTATE_SELECT_VALUES = "SELECT estate.url, image_url, price_usd, price_usd_old, price_byn, room_count, area, address FROM estate"
EstateStatus = namedtuple("EstateStatus", "new idle changed sold archived")
ESTATE_STATUS = EstateStatus(0, 1, 2, 3, 4)
exclude_estates = ("https://re.kufar.by/vi/minsk/kupit/kvartiru/188583912",
                   "https://re.kufar.by/vi/minsk/kupit/kvartiru/bez-otdelki/188537606")

def update_db(estates: list):
    log_line("INF",f"Updating db for {estates[0].search_url.url}")

    mark_sold_estates(estates)

    for estate in estates:
        if estate.url in exclude_estates : continue
        current_price = get_current_price(estate.url)
        if not current_price:
            add_estate(estate)
        elif current_price[0] != estate.price_usd:
            update_estate(estate, current_price[0])


def get_estates_for_user_notifications(user_id: int, search_url: str, status:int): 
    cursor = connection.cursor()
    query = f"{ESTATE_SELECT_VALUES} JOIN user_estate ON estate.url=user_estate.url WHERE search_url=%s AND user_id=%s AND notification_status={status}"
    cursor.execute(query, (search_url,AsIs(user_id)))
    estates_fetched = cursor.fetchall()
    estates = [Estate(*estate) for estate in estates_fetched]
    return estates


def get_search_urls_for_user(user_id: int):
    cursor = connection.cursor()
    query = "SELECT url,alias FROM user_search_url WHERE user_id=%s"
    cursor.execute(query, (AsIs(user_id),))
    urls_fetched = cursor.fetchall()
    urls = [SearchUrl(*url) for url in urls_fetched]
    return urls
  

def get_sold_estates_for_search_url(url: str):
    cursor = connection.cursor()
    query = ESTATE_SELECT_VALUES + f" JOIN user_estate ON estate.url=user_estate.url WHERE search_url=%s AND notification_status={ESTATE_STATUS.idle}"
    cursor.execute(query, (url,))
    estates_fetched = cursor.fetchall()
    estates = [Estate(*estate) for estate in estates_fetched]
    return estates


def get_current_price(url: str):
    return get_value('estate','price_usd',{'url':url}) 


def get_all_search_urls():
    return [url[0] for url in get_values('search_url','url')]


def get_user_ids():
    return [user_id[0] for user_id in get_values('tg_user','id')]


def set_notification_status_archived(user_id: int, url:str): 
    update_value('user_estate', 'notification_status', str(ESTATE_STATUS.archived), {'url':url,'user_id':user_id})


def set_notification_status_idle(user_id: int, url:str):
    update_value('user_estate', 'notification_status', str(ESTATE_STATUS.idle), {'url':url,'user_id':user_id})


def mark_sold_estates(estates: list):
    estates_urls_in_db = [estate.url for estate in get_sold_estates_for_search_url(estates[0].search_url.url)]
    estates_urls_parsed = [estate.url for estate in estates]
    sold_estates_urls = list(set(estates_urls_in_db) - set(estates_urls_parsed))
    for url in sold_estates_urls:
        update_value('user_estate', 'notification_status', str(ESTATE_STATUS.sold), {'url':url})


def add_search_url_for_user(user_id: int, search_url: SearchUrl):
    insert_value('search_url', ('url',), (search_url.url,))
    user_search_url_keys = {'user_id':user_id, 'url':search_url.url}
    insert_value('user_search_url', ('user_id','url','alias'), (user_id, *search_url), user_search_url_keys)


def add_estate(estate: Estate): 
    log_line("DB ",f"Adding new estate {estate.url}")

    insert_value('estate', ('url','image_url','search_url','price_usd','price_usd_old','price_byn','room_count','area','address'), (estate.url, estate.image_url, estate.search_url.url, estate.price_usd, estate.price_usd_old, estate.price_byn, estate.room_count, estate.area, estate.address))
    user_ids = get_values('user_search_url','user_id',{'url':estate.search_url.url})
    for user_id in user_ids:
        keys_to_check = {'user_id':user_id[0], 'url':estate.url}
        insert_value('user_estate', ('url','user_id'), (estate.url, user_id[0]), keys_to_check)


def update_estate(estate: Estate, current_price: float):
    log_line("DB ",f"Changing price for {estate.url} {current_price} -> {estate.price_usd}")

    update_value('estate', 'price_usd_old', str(current_price), {'url': estate.url})
    update_value('estate', 'price_usd', str(estate.price_usd), {'url': estate.url})
    update_value('estate', 'price_byn', str(estate.price_byn), {'url': estate.url})
    update_value('user_estate', 'notification_status', str(ESTATE_STATUS.changed), {'url': estate.url}) 




#---- shared
def check_if_exists(table:str, lookup_items) -> bool:
    cursor = connection.cursor()
    constructed_where= where_constructor(lookup_items)
    query = f"SELECT * FROM %s {constructed_where[0]}" 
    cursor.execute(query, (AsIs(table),*constructed_where[1]))
    return cursor.fetchone() is not None


def insert_value(table:str, fields:tuple, values:tuple, lookup_items: dict = {}):
    if not lookup_items:
        lookup_items = {fields[0]:values[0]}
    if check_if_exists(table,lookup_items):
        log_line("WRN", f"'{table}' with keys '{lookup_items}' already exists, skipping.....\n")
        return False
    log_line("DB ",f"Inserting to '{table}' fields '{', '.join(fields)}' with values'{values}' where '{lookup_items}'\n")

    query = "INSERT INTO %s(%s) VALUES (" + ','.join(["%s"] * len(values)) + ")"
    cursor = connection.cursor()  
    sql_log.write(str(datetime.now()) + " -- " + str(cursor.mogrify(query, (AsIs(table),AsIs(','.join(fields))) + values)) + "\n")
    cursor.execute(query,(AsIs(table),AsIs(','.join(fields))) + values) 
    connection.commit()
    cursor.close()
    return True


def get_value(table:str, select_column:str, lookup_items: dict = {}):
    constructed_where = where_constructor(lookup_items)
    query = f"SELECT %s FROM %s {constructed_where[0]}"

    cursor = connection.cursor()
    cursor.execute(query, (AsIs(select_column),AsIs(table),*constructed_where[1]))
    return cursor.fetchone()
    

def get_values(table:str, select_column:str,lookup_items: dict = {}):
    cursor = connection.cursor()
    if lookup_items:
        constructed_where = where_constructor(lookup_items)
        query = f"SELECT %s FROM %s {constructed_where[0]}"
        cursor.execute(query, (AsIs(select_column),AsIs(table),*constructed_where[1]))
    else:
        query = "SELECT %s FROM %s"
        cursor.execute(query, (AsIs(select_column),AsIs(table)))
    return cursor.fetchall()


def update_value(table: str, field_to_change: str, value_to_change: str, lookup_items):
    log_line("DB ",f"Updating table '{table}' setting '{field_to_change}' to '{value_to_change}' where '{lookup_items}'")
    constructed_where = where_constructor(lookup_items)
    query = f"UPDATE %s SET %s = %s {constructed_where[0]}"

    cursor = connection.cursor()
    cursor.execute(query, (AsIs(table), AsIs(field_to_change), value_to_change,*constructed_where[1]))
    connection.commit()
    cursor.close()


# wtf bruh
def where_constructor(lookup_items):
    fields = [AsIs(key) for key in lookup_items.keys()]
    values = lookup_items.values()
    god_why = [None]*(len(fields)+len(values))
    god_why[::2] = fields 
    god_why[1::2] = values
    return ("WHERE {}".format(" AND ".join(["%s=%s"] * len(fields))), god_why)


def log_line(type:str, line:str):
    sql_log.write(f"{datetime.now()} -- [{type}] -- {line}\n")
