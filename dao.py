#!/usr/bin/python
import psycopg2
import sys
from psycopg2.extensions import AsIs
import time
from datetime import datetime
from collections import namedtuple
import traceback

from dao import *
from dbenv import *
from object.estate import Estate
from object.search_url import SearchUrl

#
# DIRE NEED FOR REFACTORING
#

sql_log = open("connect.log", "a")
connection = psycopg2.connect(host=postgres_address, port=port, user=postgres_user, password=postgres_user_password, dbname=db_name_dev)

ESTATE_SELECT_VALUES = "SELECT url, image_url, price_usd, price_usd_old, price_byn, room_count, area, address FROM estate"

EstateStatus = namedtuple("EstateStatus", "new idle changed sold archived")
ESTATE_STATUS = EstateStatus(0, 1, 2, 3, 4)


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
    query = ESTATE_SELECT_VALUES + f" JOIN user_estate ON estate.url=user_estate.url WHERE search_url=%s AND notification_status={ESTATE_STATUS.archived}"
    cursor.execute(query, (url,))
    estates_fetched = cursor.fetchall()
    estates = [Estate(*estate) for estate in estates_fetched]
    return estates


def update_db(estates):
    sql_log.write(f"{str(datetime.now())} Starting db update...")

    estates_urls_in_db = [estate.url for estate in get_sold_estates_for_search_url(estates[0].search_url.url)]
    sold_estates_urls = list(set(estates_urls_in_db) - set([estate.url for estate in estates]))
    for url in sold_estates_urls:
        update_value('estate', 'is_sold', 'true', 'url', url)
        update_value('estate', 'is_changed', 'true', 'url', url)

    for estate in estates:
        for attempt_counter in range(0, 11):
            try:
                if not check_if_value_exists('estate', 'url', estate.url):
                    insert_value('estate', ('url','image_url','search_url','price_usd','price_usd_old','price_byn','room_count','area','address'), (estate.url, estate.image_url, estate.search_url.url, estate.price_usd, estate.price_usd_old, estate.price_byn, estate.room_count, estate.area, estate.address))
                elif get_current_price(estate.url)[0] != estate.price_usd:
                    print(f"changing {estate.url}")
                    update_value('estate', 'price_usd_old', str(get_current_price(estate.url)[0]), 'url', estate.url)
                    update_value('estate', 'price_usd', str(estate.price_usd), 'url', estate.url)
                    update_value('estate', 'price_byn', str(estate.price_byn), 'url', estate.url)
                    update_value('estate', 'is_changed', 'true', 'url', estate.url) 
                    #update_value('user_estate', 'notified_changed', 'true', 'url', estate.url) 
                break
            except Exception as e:
                print("ERROR\nFailed on estate '{}, attempt {}/10'\n{}\nWaiting 4 second and retring...\n".format(estate.url, attempt_counter, e))
                sql_log.write(str(datetime.now()) + " -- ERROR\nFailed on estate '{}'\n{}\nWaiting 4 second and retring...\n".format(estate.url, traceback.format_exc()))
                time.sleep(4)
                #connection = psycopg2.connect(host=postgres_address, user=postgres_user, password=postgres_user_password, dbname=db_name_dev
                continue



def get_current_price(url: str):
    return get_value('estate','price_usd','url',url) 

def get_all_search_urls():
    return [url[0] for url in get_values('search_url','url')]

def unflagNew(url:str): 
    update_value('estate', 'is_new', 'false', 'url', url)          

def unflagChanged(url:str):
    update_value('estate', 'is_Changed', 'false', 'url', url)          

def add_search_url_for_user(user_id: int, search_url: SearchUrl):
    insert_value('search_url', ('url',), (search_url.url,))
    user_search_url_keys = (('user_id', user_id), ('url', search_url.url))
    insert_value('user_search_url', ('user_id','url','alias'), (user_id, *search_url), user_search_url_keys)


#---- shared
def check_if_value_exists(table:str, field:str, value:str) -> bool:
    cursor = connection.cursor()
    query = "SELECT * FROM %s WHERE %s=%s"
    cursor.execute(query, (AsIs(table),AsIs(field),value))
    return cursor.fetchone() is not None

def insert_value(table:str, fields:tuple, values:tuple, keys: tuple = ()):
    if not keys:
        keys = ((fields[0], values[0]),)
    flag = False
    for key in keys:
        if not check_if_value_exists(table, key[0], key[1]):
            sql_log.write("{} with key '{}' already exists, skipping.....\n".format(table, key[0]))
            flag = True
            break
    if not flag: return False

    print("Inserting to '{}' fields '{}' key '{}'".format(table,', '.join(fields), values[0]))
    query = "INSERT INTO %s(%s) VALUES (" + ','.join(["%s"] * len(values)) + ")"
    cursor = connection.cursor()  
    #print(cursor.mogrify(query, (AsIs(table),AsIs(','.join(fields))) + values))
    sql_log.write(str(datetime.now()) + " -- " + str(cursor.mogrify(query, (AsIs(table),AsIs(','.join(fields))) + values)) + "\n")
    cursor.execute(query,(AsIs(table),AsIs(','.join(fields))) + values) 
    connection.commit()
    cursor.close()
    return True

def get_value(table:str, select_column:str, column:str = "", value:str = ""):
    cursor = connection.cursor()
    query = "SELECT %s FROM %s WHERE %s=%s" if column and value else "SELECT %s FROM %s"
    #print(cursor.mogrify(query, (AsIs(select_column),AsIs(table),AsIs(column),value)))
    cursor.execute(query, (AsIs(select_column),AsIs(table),AsIs(column),value))
    return cursor.fetchone()
    
def get_values(table:str, select_column:str, column:str = "", value:str = ""):
    cursor = connection.cursor()
    if column and value:
        query = "SELECT %s FROM %s WHERE %s=%s"
        cursor.execute(query, (AsIs(select_column),AsIs(table),AsIs(column),value))
    else:
        query = "SELECT %s FROM %s"
        cursor.execute(query, (AsIs(select_column),AsIs(table)))

    return cursor.fetchall()

def update_value(table: str, field_to_change: str, value_to_change: str, field_where: str, value_where: str):
    cursor = connection.cursor()
    query = "UPDATE %s SET %s = %s WHERE %s = %s"
    cursor.execute(query, (AsIs(table), AsIs(field_to_change), value_to_change, AsIs(field_where), value_where))
    connection.commit()
    cursor.close()
