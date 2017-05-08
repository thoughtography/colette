#!/usr/bin/env python


from uuid import uuid4

import re

from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
from telegram.ext import (Updater, InlineQueryHandler, CommandHandler, Filters,
        MessageHandler)
import logging
import sys
import requests
import urllib.parse
#from bsearch import find_book
#import bemail
import sqlite3
import random
import subprocess
import string
from telegram.ext.dispatcher import run_async


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi!')


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Help!')

def search_quote_by_id(id, photo=False):
    """Search for a quote
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        db="quotes"
        if photo:
            db="photos"
        c.execute('select * from {} where x=?'.format(db), (id,))
        quote = c.fetchone()[-1]
    return quote

def search_quote(search_str, photo=False):
    """Search for a quote
    """
    s_str = "%%%{0}%%%".format(search_str)
    with sqlite3.connect('quipper') as conn:
        db="quotes"
        if photo:
            db="photos"
        c = conn.cursor()
        c.execute('select * from {} where quote like ? order by date desc'
                ' limit 1'.format(db), (s_str,))
        quote = c.fetchone()[-1]
    return quote

def get_random_quote(user=None, photo=False):
    """Get random quote from global or from user
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        db="quotes"
        if photo:
            db="photos"
        c.execute('select * from {}'.format(db))
        return random.choice(c.fetchall())[-1]

@run_async
def figlet(bot, update):
    """Return a figlet string
    """
    fig_str = ' '.join(update.message.text.split()[1:])
    if fig_str.startswith('-'):
        bot.sendMessage(update.message.chat_id, text='No, dude')
    else:

        fig = subprocess.check_output(['/home/sloopdoop/tmp/figlet/figlet',
            '-d', '/home/sloopdoop/tmp/figlet/fonts', 
            '{}'.format(fig_str)]).decode()
        fig_str = """```{}```""".format(fig)
        bot.sendMessage(update.message.chat_id, text=fig_str,
                parse_mode="Markdown")

def delete_quote_by_id(bot, update):
    """Delete a quote from telegram
    """

    id = update.message.from_user.id
    if id != 127511991:
        return
    quote_id = update.message.text.split()[1]

    try:
        with sqlite3.connect('quipper') as conn:
            c = conn.cursor()
            c.execute('delete from quotes where x=?', (quote_id, ))
            conn.commit()
            bot.sendMessage(update.message.chat_id, text="I deleted the quote "
                    " with ID {}".format(quote_id))
    except Exception as e:
        bot.sendMessage(update.message.chat_id, text="I couldn't delete the"
                " quote. ({})".format(e))

def get_random_user_quote(user, photo=False):
    """Get random quote from a user
    """
    db="quotes"
    if photo:
        db="photos"
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where username=?', (user,))
        id = c.fetchone()[0]
        c.execute('select * from {} where owner=? order by date'
                ' desc'.format(db) , (id,
            ))
        quote = random.choice(c.fetchall())
    return compile_quote(quote, user)

def get_last_quote(user, photo=False):
    """Get last quote from a user
    """
    db="quotes"
    if photo:
        db="photos"
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where username=?', (user,))
        id = c.fetchone()[0]
        c.execute('select * from {} where owner=? order by date desc'
                ' limit 1'.format(db), (id, ))
        quote = c.fetchone()
        if photo:
            photo_id = quote[4]
        return photo_id
    return compile_quote(quote, user)

def compile_quote(quote, user):
    quote_id = quote[0]
    quote_date = quote[1]
    quote_text = quote[3]
    return "[{0}]At {1} @{2} said ``{3}''".format(quote_id, quote_date, user,
            quote_text)

def get_quote(bot, update):
    """Get a quote based on the request
    """
    line_s = update.message.text.split()

    if len(line_s)<=1:
        bot.sendMessage(update.message.chat_id, text=get_random_quote())
    elif line_s[1] == '-l':
        user = line_s[2].strip('@').strip()
        bot.sendMessage(update.message.chat_id, text=get_last_quote(user))
    elif line_s[1] == '-s':
        search_str = ' '.join(line_s[2:])
        bot.sendMessage(update.message.chat_id, text=search_quote(search_str))
    elif line_s[1] == '-i':
        id = line_s[2]
        bot.sendMessage(update.message.chat_id, text=search_quote_by_id(id))
    else:
        user = line_s[1].strip('@').strip()
        bot.sendMessage(update.message.chat_id,
                text=get_random_user_quote(user))

#def restart_git(bot, update):
#    """Restart the bot by exiting, forcing the container to reboot
#    """
#    try:
#        git = subprocess.check_output(['/usr/bin/git', 'pull', '/usr/src/app'])
#    except exception as e:
#        pass
#    sys.exit()

@run_async
def math(bot, update):
    text = update.message.text.split()
    try:
        if len([g for g in text[1] if g in string.ascii_letters])>0:
            raise
        math_result = eval(text[1])
    except Exception as e:
        math_result = 0
    bot.sendMessage(update.message.chat_id, text=math_result)


def channel_logger(bot, update):
    """Quip store
    """
    time_or_times = 'times'
    global buzzwords
    global words
    text = update.message.text
    text_date = update.message.date
    username = update.message.from_user.username
    channel = update.message.chat.title
    output = '@{} has said '.format(username)
    for word in words:
        lc_text = text.lower()
        if word in text.lower():
            c = len(lc_text.split(word))-1
            # Reply with the count of gays.
            if word not in buzzwords.keys():
                buzzwords[word] = {}
            gaycount = buzzwords[word].setdefault(username, 0) + c
            if gaycount == 1:
                time_or_times = 'time'
            buzzwords[word][username] += c
            if 'time' in output:
                output += "; '{}' {} {}".format(word, gaycount, time_or_times)
            else:
                output += "'{}' {} {}".format(word, gaycount, time_or_times)
    if 'time' in output:
        bot.sendMessage(update.message.chat_id, text="{}"
                " this session".format(output))
    with open('telegram_log', 'a') as f: 
        f.write('{0} ({1}) [{2}]: {3}\n'.format(text_date, channel, username,
            text))

def quipper_forward(bot, update):
    """Quip store
    """
    quip = update.message.text
    owner = update.message.forward_from.id
    quote_date = update.message.forward_date
    username = update.message.forward_from.username
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where id=?', (owner,))
        if not c.fetchone():
            c.execute('insert into users values (?, ?)', (owner, username))
        print('insert into quotes (date, owner, quote) values ({}, {}, {})',
                (quote_date, owner, quip))
        c.execute('insert into quotes (date, owner, quote) values (?, ?, ?)',
                (quote_date, owner, quip))
        conn.commit()

def quipper(bot, update):
    """Quip store
    """
    quip = update.message.reply_to_message.text
    owner = update.message.reply_to_message.from_user.id
    quote_date = update.message.reply_to_message.date
    username = update.message.reply_to_message.from_user.username
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where id=?', (owner,))
        if not c.fetchone():
            c.execute('insert into users values (?, ?)', (owner, username))
        print('insert into quotes (date, owner, quote) values ({}, {}, {})',
                (quote_date, owner, quip))
        c.execute('insert into quotes (date, owner, quote) values (?, ?, ?)',
                (quote_date, owner, quip))
        conn.commit()


def escape_markdown(text):
    """Helper function to escape telegram markup symbols"""
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)

def register(bot, update):
    userID = update.message.from_user['id']
    email = update.message.text.split()[1]
    try:
        with sqlite3.connect('books') as conn:
            c = conn.cursor()
            c.execute("insert into users values (?, ?)", (userID, email))
            conn.commit()
        bot.sendMessage(update.message.chat_id, text="You have been added to the"
                " database with the email address '{0}'".format(email))
    except Exception as e:
        bot.sendMessage(update.message.chat_id, text="You are already in the"
                " database")

def email(bot, update):
    userID = update.message.from_user['id']
    with sqlite3.connect('books') as conn:
        c = conn.cursor()
        c.execute("select * from users where telegram_name=?", (userID, ))
        email_addr = c.fetchone()[1]
    uuid = update.message.text.split()[1]
    mail_output = bemail.find_book(uuid, True, str(email_addr)) 
    if not mail_output or mail_output == "null":
        bot.sendMessage(update.message.chat_id, text="I emailed your book to"
                " you")


def search(bot, update):
    query = update.message.text.split(' ', 1)[1]
    if len(query)<=2:
        bot.sendMessage(update.message.chat_id, text="You gotta ask for a book")
    #return str(find_book(query))
    book_results = find_book(query)
    msg_reply = '\n'.join(book_results.split('\n')[:3])
    bot.sendMessage(update.message.chat_id, text=str(msg_reply))

@run_async
def get_ifl_link(bot, update):

    query = update.message.text.split(' ', 1)[1]
    var = requests.get( r'http://www.google.com/search?q={0}&btnI'.format(
        urllib.parse.quote_plus(query) ))

    bot.sendMessage(update.message.chat_id, text=var.url)

def inlinequery(bot, update):
    query = update.inline_query.query
    results = list()

    results.append(InlineQueryResultArticle(id=uuid4(), title="Caps",
        input_message_content=InputTextMessageContent( query.upper())))

    results.append(InlineQueryResultArticle(id=uuid4(), title="Bold",
        input_message_content=InputTextMessageContent( "*%s*" %
            escape_markdown(query), parse_mode=ParseMode.MARKDOWN)))

    results.append(InlineQueryResultArticle(id=uuid4(), title="Italic",
        input_message_content=InputTextMessageContent( "_%s_" %
            escape_markdown(query), parse_mode=ParseMode.MARKDOWN)))

    bot.answerInlineQuery(update.inline_query.id, results=results)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def seve_pikjur(bot, update):
    """Save a picture and returns it's identifier for recallability"""
    # update.message.reply_to_message

    quip = update.message.reply_to_message.text
    owner = update.message.reply_to_message.from_user.id
    quote_date = update.message.reply_to_message.date
    photo_id = update.message.reply_to_message.photo[-1].file_id
    username = update.message.reply_to_message.from_user.username
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where id=?', (owner,))
        if not c.fetchone():
            c.execute('insert into users values (?, ?)', (owner, username))
        print('insert into quotes (date, owner, quote, photo_id) values ({},'
                ' {}, {}, {})', (quote_date, owner, quip, photo_id))
        c.execute('insert into photos (date, owner, quote, photo_id) values'
                ' (?, ?, ?, ?)', (quote_date, owner, quip, photo_id))
        conn.commit()
        c.execute('select * from photos order by x desc limit 1')
    bot.sendMessage(update.message.chat_id, c.fetchall()[0])

def get_pikjur(bot, update):
    line_s = update.message.text.split()

    if len(line_s)<=1:
        bot.sendPhoto(update.message.chat_id,
                photo=get_random_quote(photo=True))
    elif line_s[1] == '-l':
        user = line_s[2].strip('@').strip()
        bot.sendPhoto(update.message.chat_id, photo=get_last_quote(user,
            photo=True))
    elif line_s[1] == '-s':
        search_str = ' '.join(line_s[2:])
        bot.sendPhoto(update.message.chat_id, photo=search_quote(search_str,
            photo=True))
    elif line_s[1] == '-i':
        id = line_s[2]
        bot.sendPhoto(update.message.chat_id, photo=search_quote_by_id(id,
            photo=True))
    else:
        user = line_s[1].strip('@').strip()
        bot.sendPhoto(update.message.chat_id,
                photo=get_random_user_quote(user, photo=True))




def main():
    global buzzwords
    global words
    words = ['gay', 'something something', 'nigger', 'i mean', 'guttersnipe']
    buzzwords = {}
    # Create the Updater and pass it your bot's token.
    updater = Updater("239641029:AAET8NqR9uef_JccleEY9oHsZsdvw4-ZD7Y")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("register", register))
    #dp.add_handler(CommandHandler("bemail", email))
    #dp.add_handler(CommandHandler("bsearch", search))
    dp.add_handler(CommandHandler("google", get_ifl_link))
    dp.add_handler(CommandHandler("Google", get_ifl_link))
    dp.add_handler(CommandHandler("quote", quipper))
    dp.add_handler(CommandHandler("quip", quipper))
    dp.add_handler(CommandHandler("getq", get_quote))
    dp.add_handler(CommandHandler("getquote", get_quote))
    dp.add_handler(CommandHandler("delquote", delete_quote_by_id))
    dp.add_handler(CommandHandler("fig", figlet))
    dp.add_handler(CommandHandler("math", math))
    dp.add_handler(CommandHandler("seve_pikjur", seve_pikjur))
    dp.add_handler(CommandHandler("get_pikjur", get_pikjur))
    #dp.add_handler(CommandHandler("restart", restart_git))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(InlineQueryHandler(inlinequery))

    # log all errors
    dp.add_error_handler(error)

    # Add message handler for quips!
    #dp.add_handler(MessageHandler([Filters.text], quipper))
    dp.add_handler(MessageHandler(Filters.text, channel_logger))

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
