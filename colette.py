#!/usr/bin/env python


from uuid import uuid4

import re

from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
from telegram.ext import (Updater, InlineQueryHandler, CommandHandler, Filters,
        MessageHandler)
import logging
import requests
import urllib.parse
#from bsearch import find_book
#import bemail
import sqlite3
import random
import subprocess
import string
from Markov import Markov
from pymarkovchain import MarkovChain
from telegram.ext.dispatcher import run_async

mc = MarkovChain("./markov")

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

def search_quote_by_id(id):
    """Search for a quote
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from quotes where x=?', (id,))
        quote = c.fetchone()[3]
    return quote

def search_quote(search_str):
    """Search for a quote
    """
    s_str = "%%%{0}%%%".format(search_str)
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from quotes where quote like ? order by date desc'
                ' limit 1', (s_str,))
        quote = c.fetchone()[3]
    return quote

def get_random_quote(user=None):
    """Get random quote from global or from user
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from quotes')
        return random.choice(c.fetchall())[3]

@run_async
def figlet(bot, update):
    """Return a figlet string
    """
    fig_str = ' '.join(update.message.text.split()[1:])
    if fig_str.startswith('-'):
        bot.sendMessage(update.message.chat_id, text='No, dude')
    else:

        fig = subprocess.check_output(['/usr/bin/figlet',
            '{}'.format(fig_str)]).decode()
        fig_str = """.
    ```{}```""".format(fig)
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

def get_random_user_quote(user):
    """Get random quote from a user
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where username=?', (user,))
        id = c.fetchone()[0]
        c.execute('select * from quotes where owner=? order by date desc' , (id,
            ))
        quote = random.choice(c.fetchall())
        quote_id = quote[0]
        quote_date = quote[1]
        quote_text = quote[3]
    return "[{0}]At {1} @{2} said ``{3}''".format(quote_id, quote_date, user,
            quote_text)

def get_last_quote(user):
    """Get last quote from a user
    """
    with sqlite3.connect('quipper') as conn:
        c = conn.cursor()
        c.execute('select * from users where username=?', (user,))
        id = c.fetchone()[0]
        c.execute('select * from quotes where owner=? order by date desc'
                ' limit 1', (id, ))
        quote = c.fetchone()
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
    if line_s[1] == '-l':
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

def restart_git(bot, update):
    """Restart the bot by exiting, forcing the container to reboot
    """
    git = subprocess.check_output(['git', 'pull'])
    sys.exit()

@run_async
def markov(bot, update):
    """Return a string of text from markov
    """
    text = update.message.text.split()
    if len(text) > 1:
        seed = ' '.join(text[1:])
        markov_text = mc.generateStringWithSeed(seed)
    else:
        markov_text = mc.generateString()
    #with open('markov') as markov_file:
    #    chain = Markov(markov_file)
    #    markov_text = chain.generate_markov_text()
    bot.sendMessage(update.message.chat_id, text=markov_text)

def channel_logger(bot, update):
    """Quip store
    """
    global buzzwords
    global words
    text = update.message.text
    text_date = update.message.date
    username = update.message.from_user.username
    channel = update.message.chat.title
    for word in words:
        if word in text.lower():
            # Reply with the count of gays.
            if word not in buzzwords.keys():
                buzzwords[word] = {}
            gaycount = buzzwords[word].setdefault(username, 0) + 1
            buzzwords[word][username] += 1
            bot.sendMessage(update.message.chat_id, text="{} has said '{}' {} "
                    "times this session".format(username, word, gaycount))
    with open('markov_db', 'a') as f: 
        f.write('{0}\n'.format(text))
    mc.generateDatabase(text)

    dbdump = mc.dumpdb()
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


def main():
    global buzzwords
    global words
    words = ['gay', 'something something', 'nigger']
    buzzwords = {}
    # Create the Updater and pass it your bot's token.
    updater = Updater("239641029:AAET8NqR9uef_JccleEY9oHsZsdvw4-ZD7Y")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(CommandHandler("bemail", email))
    dp.add_handler(CommandHandler("bsearch", search))
    dp.add_handler(CommandHandler("google", get_ifl_link))
    dp.add_handler(CommandHandler("Google", get_ifl_link))
    dp.add_handler(CommandHandler("quote", quipper))
    dp.add_handler(CommandHandler("quip", quipper))
    dp.add_handler(CommandHandler("getq", get_quote))
    dp.add_handler(CommandHandler("getquote", get_quote))
    dp.add_handler(CommandHandler("delquote", delete_quote_by_id))
    dp.add_handler(CommandHandler("fig", figlet))
    dp.add_handler(CommandHandler("markov", markov))
    dp.add_handler(CommandHandler("restart", restart_git))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(InlineQueryHandler(inlinequery))

    # log all errors
    dp.add_error_handler(error)

    # Add message handler for quips!
    #dp.add_handler(MessageHandler([Filters.text], quipper))
    dp.add_handler(MessageHandler([Filters.text], channel_logger))

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
