#!/usr/bin/python
import requests 
import sys

from scrapper import get_estates,get_page_count
from env import *
from dao import *

from object.estate import Estate
from object.search_url import SearchUrl

def main():
    log_line("INF",f"Starting db update")
    search_urls = get_all_search_urls()
    for url in search_urls:
        print(f"Parsing {url}")
        page_count = get_page_count(url)
        print(f"Pages:{page_count}")
        estates = []
        for page in range(1, page_count + 1):
            print(page)
            estates += get_estates(SearchUrl(url,"alias_placeholder"), page)
        update_db(estates)
    connection.close()
    log_line("INF",f"Ending db update...\n\n")



if __name__ == "__main__":
    main()
