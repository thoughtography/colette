#!/usr/bin/env python

import sqlite3
from telegram.ext.dispatcher import run_async

class User:
    def __init__(self, db='quipper', testing=False):
        """Open a new database connection and build registries"""
        self.db = db
        self.users_table = 'users'
        self.privileges_table = 'privileges'
        #if testing:
        #    self.quotes_table += '_test'
        #    self.photos_table += '_test'


    def check_user_exist(self, id, username):
        with sqlite3.connect('quipper') as conn:
            c = conn.cursor()
            c.execute('select * from {} where id=?'.format(self.users_table), 
                    (id,))
            user = c.fetchone()
            if not user:
                c.execute('insert into {} values (?,'
                        ' ?)'.format(self.users_table), (id, username))
            elif user[1] != username:
                c.execute('update {} set username=? where'
                        ' id=?'.foramt(self.users_table), (username, id))

    def register(self, bot, update):
        userID = update.message.from_user['id']
        email = update.message.text.split()[1]
        try:
            with sqlite3.connect('quipper') as conn:
                c = conn.cursor()
                c.execute("insert into users values (?, ?)", (userID, email))
                self.db.commit()
                bot.sendMessage(update.message.chat_id, text="You have been"
                        " added to the database with the email address"
                        " '{0}'".format( email))
        except Exception as e:
            bot.sendMessage(update.message.chat_id, text="You are already in" 
                    " the database")

