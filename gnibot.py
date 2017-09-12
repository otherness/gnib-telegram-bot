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
Basic notification Bot, it looks for available appointments to GNIB office and posts updates into specific channel.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.

TODO:

- add check whether or not http request was successful
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job
import logging
import requests
import urllib3
import csv
import os.path
import botconf

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class State:
    """Class represents state of scheduling calendar"""
    avail_dates = []


prev_state = State()

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi. I serve only one purpose at the moment. I post updates to INIS Appointments channel. I can\'t do anything else.')


def help(bot, update):
    update.message.reply_text('This bot serves a single purpose: it posts updates to INIS Appointments channel. That\'s it.')


def shrug(bot, update):
    update.message.reply_text('¯\_(ツ)_/¯')


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def parse_dates(resp_dict):
    lst = []
    for entry in resp_dict['slots']:
        lst.append(entry['time'])
    logger.info('List of dates returned in http response: {list}'.format(list=lst))
    return lst


def touch(path):
    with open(path, 'a'):
        os.utime(path, None)


def save_state(state_list):
    with open('./state.csv', 'w') as state_file:
        wr = csv.writer(state_file, quoting=csv.QUOTE_ALL)
        wr.writerow(state_list)


def load_state():
    with open('./state.csv') as state_file:
        reader = csv.reader(state_file,delimiter=',')
        state_list = list(reader)
        if state_list == []:
            logger.info('The empty state list has been loaded.')
            return []
        else:
            logger.info('The following list has been loaded: [\'{lst}\'] '.format(lst='\', \''.join(state_list[0])))
            return state_list[0]


def initialize():
    if os.path.exists('./state.csv'):
        logger.info('State file exists, trying to load state...')
        prev_state.avail_dates = load_state()
    else:
        logger.info('State file doesn\'t exist, creating an empty one.')
        touch('./state.csv')


def callback_query(bot, job):

    # Get nearest appointments from INIS site
    response = requests.get('https://burghquayregistrationoffice.inis.gov.ie/Website/AMSREG/AMSRegWeb.nsf/(getAppsNear)?openpage&cat=Work&sbcat=All&typ=New', verify=False)
    resp_dict = response.json()

    # if no dates available - change prev_state to empty list and exit
    if 'empty' in resp_dict.keys():
        logger.info('No dates available')
        # if state changed - update files and state, otherwise do nothing
        if prev_state.avail_dates == []:
            pass
        else:
            prev_state.avail_dates = []
            save_state([])

    # if dates are available - get them as python list and compare to previous answer, exit if no changes
    else:
        state = parse_dates(resp_dict)
        if state == prev_state.avail_dates: # the response didn't change since last query, do nothing
            logger.info('No changes since last time')
            pass
        else:
            new_list = (list(set(state).difference(prev_state.avail_dates))) # get dates that were not in the previous update
            logger.info('New entries in this response: {new}'.format(new=new_list))
            #bot.send_message(chat_id=botconf.chat_id, text='New appointment dates available:\n' + '\n'.join(new_list)) # post update to the channel
            prev_state.avail_dates = state
            save_state(state)


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(botconf.token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Get the JobQueue object for scheduling
    jq = updater.job_queue

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, shrug))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # try to read state file, if no file present - create one with an empty state
    initialize()

    # Run callback function each 60 seconds
    jq.run_repeating(callback_query, interval=60, first=1)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
