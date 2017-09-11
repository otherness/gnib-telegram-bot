#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Simple Bot to notify about INIS appontments that becomes available
"""
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job
import logging
import requests
import api_token
import urllib3

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Chat ID for INIS appointments channel
chat_id = -1001148154214

class State:
    """Class represents state of scheduling calendar"""
    avail_dates = []


prev_state = State()

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi!')


def help(bot, update):
    update.message.reply_text('Help!')


def echo(bot, update):
    update.message.reply_text(update.message.text)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))



def parse_dates(resp_dict):
    lst = []
    for entry in resp_dict['slots']:
        lst.append(entry['time'])
    print('List of dates returned in http response: {list}'.format(list=lst))
    return lst

def callback_query(bot, job):

    # Get nearest appointments from INIS site
    response = requests.get('https://burghquayregistrationoffice.inis.gov.ie/Website/AMSREG/AMSRegWeb.nsf/(getAppsNear)?openpage&cat=Work&sbcat=All&typ=New', verify=False)
    resp_dict = response.json()

    # if no dates available - change prev_state to empty list and exit
    if 'empty' in resp_dict.keys():
        prev_state.avail_dates = []

    # if dates are available - get them as python list and compare to previous answer, exit if no changes
    else:
        state = parse_dates(resp_dict)
        if state == prev_state.avail_dates: # the response didn't change since last query, do nothing
            print('No changes since last time')
            pass
        else:
            new_list = (list(set(state).difference(prev_state.avail_dates))) # get dates that were not in the previous update
            print('New entries in this response: {new}'.format(new=new_list))
            bot.send_message(chat_id=chat_id, text='New appointment dates available:\n' + '\n'.join(new_list))
            prev_state.avail_dates = state
def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(api_token.token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Get the JobQueue object for scheduling
    jq = updater.job_queue

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    #job_minute = Job(callback_minute)

    jq.run_repeating(callback_query, interval=60, first=1)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()


# proxies = {
#     'http': 'http://127.0.0.1:8080',
#     'https': 'http://127.0.0.1:8080',
# }
#
# response = requests.get('https://burghquayregistrationoffice.inis.gov.ie/Website/AMSREG/AMSRegWeb.nsf/(getAppsNear)?openpage&cat=Work&sbcat=All&typ=New', proxies=proxies, verify=False)
#
## if no dates available, returns {"empty":"TRUE"}
#
# print(format(response.json()))
