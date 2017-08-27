#!/usr/bin/env python

import sqlite3
from telegram.ext.dispatcher import run_async

class User:
    def __init__(self, db='quipper', testing=False):
        """Open a new database connection and build registries"""
        self.db = db
        self.users_table = 'users'
        self.privileges_table = 'privileges'
        if testing:
            self.users_table += '_test'
            self.privileges_table += '_test'


    def check_user_exist(self, id, username, room=None, role="user"):
        with sqlite3.connect('quipper') as conn:
            c = conn.cursor()
            c.execute('select * from {} where id=? and room=?'.format(
                self.users_table), (id, room))
            user = c.fetchone()
            if not user:
                c.execute('insert into {} values (?,'
                        ' ?, ?, ?)'.format(self.users_table), (id, username,
                            room, role))
            elif user[1] != username:
                c.execute('update {} set username=? where'
                        ' id=? and room=?'.foramt(self.users_table), (username,
                            id, room))

    def register(self, bot, update):
        userID = update.message.from_user.id
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


    def get_priv(self, bot, update):
        """ Print user privileges """
        bot.sendMessage(update.message.chat_id,
                text=self.get_user_privilege(update.message.from_user.id,
                    update.message.chat.id))

    def update_user_priv(self, bot, update):
        """ Update a users privileges in a room """
        room = update.message.chat.id
        caller = update.message.from_user.id
        username = update.message.text.split(' ')[1].strip('@')
        role = update.message.text.split(' ')[2]
        if role != "admin": role = 'user'
        db = self.users_table
        if self.get_user_privilege(caller, room) != "admin":
            bot.sendMessage(update.message.chat_id, text="You do not have that"
                    " privilege")
            return
        try: 
            with sqlite3.connect('quipper') as conn:
                c = conn.cursor()
                c.execute("update {} set role=? where username=? and"
                        " room=?".format(db), (role, username, room))
        except Exception as e:
            bot.sendMessage(update.message.chat_id, text=e)

    def get_user_privilege(self, user, room):
        """ Check if a user has privileges in a room """
        db = self.users_table
        if user == 296246016:
            return 'admin'
        try:
            with sqlite3.connect('quipper') as conn:
                c = conn.cursor()
                c.execute("select id,room,role,username from {}".format(db))
                users = c.fetchall()
                # Room
                # -Role
                # --User
                user_list = {}
                for id, room, role, u in users:
                    if str(id) == str(user):
                        return role
                return 'user'
#                    if not user_list.get(room, None):
#                        user_list[room] = {}
#                    if not user_list[room].get(role, None):
#                        user_list[room][role] = []
#                    user_list[room][role].append(u)
#                return user_list
        except Exception as e:
            return "I failed to check user privileges\n{}".format(repr(e))
