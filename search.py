#!/usr/bin/env python

import sqlite3
from telegram.ext.dispatcher import run_async
import urllib.parse
import requests
from googlefinance import getQuotes
from google import google

class Search:
    def __init__(self, testing=False):
        """ Do searches for things (google, stocks, images, etc) """
    @run_async
    def get_ifl_link(self, bot, update):
        query = update.message.text.split(' ', 1)[1]
        search_results = google.search(query)
        result = search_results[0]
        bot.sendMessage(update.message.chat_id, text=result.link)

    def get_stock(self, bot, update):
        """ Get stock quotes """
        line_s = update.message.text.split()
        ticker = line_s[1].upper()
        stock = getQuotes(ticker)
        last_price = stock[0]["LastTradePrice"]
        last_time = stock[0]["LastTradeDateTimeLong"]
        div = stock[0].get("Dividend")
        index = stock[0]["Index"]
        bot.sendMessage(update.message.chat_id, "{{{0}}}[{1}] ${2} @{3} ({4})".format(index, ticker,
            last_price, last_time, div))

    def search(self, bot, update):
        query = update.message.text.split(' ', 1)[1]
        if len(query)<=2:
            bot.sendMessage(update.message.chat_id, text="You gotta ask for a book")
        #return str(find_book(query))
        book_results = find_book(query)
        msg_reply = '\n'.join(book_results.split('\n')[:3])
        bot.sendMessage(update.message.chat_id, text=str(msg_reply))

