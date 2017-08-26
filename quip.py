#!/usr/bin/env python

import sqlite3
from telegram.ext.dispatcher import run_async

class Quip:
    def __init__(self, db='quipper', testing=False):
        """Open a new database connection and build registries"""
        self.db = sqlite3.connect(db)
        self.quotes_table = 'quotes'
        self.photos_table = 'photos'
        if testing:
            self.quotes_table += '_test'
            self.photos_table += '_test'

def search_quote_by_tag(tag, room, photo=False):
    """Search for a quote
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        db = quotes_table
        if photo:
            db = photos_table
        tag = "%%%{0}%%%".format(tag)
        print("select * from {0} where tag like {1} and room={2}".format(db,
            tag, room))
        c.execute('select * from {} where tag like ? and room=?'.format(db),
                (tag, room))
        quote = c.fetchone()
        if photo:
            photo_id = quote[4]
            return photo_id
    return compile_quote(quote, user)

def search_quote_by_id(id, room, photo=False):
    """Search for a quote
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        db = quotes_table
        if photo:
            db = photos_table
        c.execute('select * from {} where x=? and room=?'.format(db), (id,
            room))
        quote = c.fetchone()
        if photo:
            photo_id = quote[4]
            return photo_id
    return compile_quote(quote)

def search_quote(search_str, room, photo=False):
    """Search for a quote
    """
    s_str = "%%%{0}%%%".format(search_str)
    with sqlite3.connect('quipper') as conn:
        db = quotes_table
        if photo:
            db = photos_table
        c = conn.cursor()
        c.execute('select * from {} where quote like ? and room=? order by date desc'
                ' limit 1'.format(db), (s_str, room))
        quote = c.fetchone()
        if photo:
            photo_id = quote[4]
            return photo_id
    return compile_quote(quote)

def get_random_quote(room, user=None, photo=False):
    """Get random quote from global or from user
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        db = quotes_table
        if photo:
            db = photos_table
        c.execute('select * from {} where room=?'.format(db), (room,))
        quote = random.choice(c.fetchall())
        if photo:
            photo_id = quote[4]
            return photo_id
    return compile_quote(quote, user)

def delete_quote_by_id(bot, update):
    """Delete a quote from telegram
    """
    room = update.message.chat.id
    db = quotes_table
    id = update.message.from_user.id
    if id != 127511991:
        return
    quote_id = update.message.text.split()[1]

    try:
        with sqlite3.connect('quipper') as conn:
            c = conn.cursor()
            c.execute('delete from {0} where x=? and room=?'.format(db),
                    (quote_id, room))
            conn.commit()
            bot.sendMessage(update.message.chat_id, text="I deleted the quote "
                    " with ID {}".format(quote_id))
    except Exception as e:
        bot.sendMessage(update.message.chat_id, text="I couldn't delete the"
                " quote. ({})".format(e))

def get_random_user_quote(user, room, photo=False):
    """Get random quote from a user
    """
    db = quotes_table
    if photo:
        db = photos_table
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where username=?', (user,))
        id = c.fetchone()[0]
        c.execute('select * from {} where owner=? and room=? order by date'
                ' desc'.format(db) , (id, room))
        quote = random.choice(c.fetchall())
        if photo:
            photo_id = quote[4]
            return photo_id
    return compile_quote(quote, user)

def get_last_quote(user, room, photo=False):
    """Get last quote from a user
    """
    db = quotes_table
    if photo:
        db = photos_table
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where username=?', (user,))
        id = c.fetchone()[0]
        c.execute('select * from {} where owner=? and room=? order by date desc'
                ' limit 1'.format(db), (id, room))
        quote = c.fetchone()
        if photo:
            photo_id = quote[4]
            return photo_id
    return compile_quote(quote, user)

def compile_quote(quote, user=None):
    quote_id = quote[0]
    if not user:
        with sqlite3.connect('quipper') as conn:
            c = conn.cursor()
            c.execute('select * from users where id=?', (quote[2],))
            user = c.fetchone()[1]
    quote_date = quote[1]
    quote_text = quote[3]
    return "[{0}]At {1} @{2} said ``{3}''".format(quote_id, quote_date, user,
            quote_text)

def get_quote(bot, update):
    """Get a quote based on the request
    """
    room = update.message.chat.id
    line_s = update.message.text.split()

    if len(line_s)<=1:
        bot.sendMessage(update.message.chat_id,
                text=get_random_quote(room))
    elif line_s[1] == '-l':
        user = line_s[2].strip('@').strip()
        bot.sendMessage(update.message.chat_id, text=get_last_quote(user, room))
    elif line_s[1] == '-s':
        search_str = ' '.join(line_s[2:])
        bot.sendMessage(update.message.chat_id, text=search_quote(search_str,
            room))
    elif line_s[1] == '-i':
        id = line_s[2]
        bot.sendMessage(update.message.chat_id, text=search_quote_by_id(id, room))
    else:
        user = line_s[1].strip('@').strip()
        bot.sendMessage(update.message.chat_id,
                text=get_random_user_quote(user, room))

def quipper_forward(bot, update):
    """Quip store
    """
    db = quotes_table
    quip = update.message.text
    owner = update.message.forward_from.id
    quote_date = update.message.forward_date
    username = update.message.forward_from.username
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        check_user_exist(owner, username)
        print('insert into {0} (date, owner, quote, room) values ({1}, {2},'
                ' {3}, {4})', (db, quote_date, owner, quip, room))
        c.execute('insert into {0} (date, owner, quote, room) values (?, ?,'
                ' ?, ?)'.format(db), (quote_date, owner, quip, room))
        conn.commit()

def quipper(bot, update):
    """Quip store
    """
    db = quotes_table
    quip = update.message.reply_to_message.text
    owner = update.message.reply_to_message.from_user.id
    quote_date = update.message.reply_to_message.date
    username = update.message.reply_to_message.from_user.username
    room = update.message.chat.id
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        check_user_exist(owner, username)
        print('insert into {0} (date, owner, quote, room) values ({1}, {2},'
                ' {3}, {4})', (quote_date, owner, quip, room))
        c.execute('insert into {0} (date, owner, quote, room) values (?, ?,'
                ' ?, ?)'.format(db), (quote_date, owner, quip, room))
        conn.commit()

def seve_pikjur(bot, update):
    """Save a picture and returns it's identifier for recallability"""
    # update.message.reply_to_message

    db = photos_table
    room = update.message.chat.id
    text = ' '.join(update.message.text.split()[1:])
    quip = update.message.reply_to_message.text
    owner = update.message.reply_to_message.from_user.id
    quote_date = update.message.reply_to_message.date
    photo_id = update.message.reply_to_message.photo[-1].file_id
    username = update.message.reply_to_message.from_user.username
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        check_user_exist(owner, username)
        print('insert into {} (date, owner, quote, tag, photo_id) values'
                ' ({},' ' {}, {}, {})', (db, quote_date, owner, quip, text,
                photo_id, room))
        c.execute('insert into {} (date, owner, quote, tag, photo_id, room)'
                ' values (?, ?, ?, ?, ?, ?)'.format(db), (quote_date, owner,
                    quip, text, photo_id, room))
        conn.commit()
        c.execute('select * from {} where room=? order by x desc limit'
                ' 1'.format(db), (room,))
    bot.sendMessage(update.message.chat_id, c.fetchall()[0])

def get_pikjur(bot, update):
    room = update.message.chat.id
    line_s = update.message.text.split()

    if len(line_s)<=1:
        bot.sendPhoto(update.message.chat_id,
                photo=get_random_quote(room, photo=True))
    elif line_s[1] == '-l':
        user = line_s[2].strip('@').strip()
        bot.sendPhoto(update.message.chat_id, photo=get_last_quote(user,
            room, photo=True))
    elif line_s[1] == '-s':
        search_str = ' '.join(line_s[2:])
        bot.sendPhoto(update.message.chat_id, photo=search_quote(search_str,
            room, photo=True))
    elif line_s[1] == '-i':
        id = line_s[2]
        bot.sendPhoto(update.message.chat_id, photo=search_quote_by_id(id,
            room, photo=True))
    elif line_s[1] == '-t':
        tag = ' '.join(line_s[2:])
        bot.sendPhoto(update.message.chat_id, photo=search_quote_by_tag(tag,
            room, photo=True))
    else:
        user = line_s[1].strip('@').strip()
        bot.sendPhoto(update.message.chat_id,
                photo=get_random_user_quote(user, room, photo=True))

