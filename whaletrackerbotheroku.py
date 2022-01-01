import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

import requests
import sqlite3
import json
import logging
import time
import os
PORT = int(os.environ.get('PORT', 8443))

telegram_bot_token = "xxxxxxxxxxxxxxxxxxxxxxxxx" # secret bot token key

approved_users = [] # can be users, groups, channels chat_ids

updater = Updater(token=telegram_bot_token, use_context=True)
dispatcher = updater.dispatcher



#-------------------- periodic wallet trackers ------------------------------#
def start(update,context): #func to start periodic checks on wallet addresses
    chat_id = update.effective_chat.id
    print(chat_id)
    if chat_id != xxxxxx: # prevent other unautorised users
        context.bot.send_message(chat_id=update.message.chat_id, text='You are not authorised to use this bot!')
    else:
        context.job_queue.run_repeating(search, 30, context=update.message.chat_id) # runs checks every 60 seconds

def search(context):
    message = ""
    
    con = sqlite3.connect('whale_list.db') # connect to db
    cur = con.cursor()
    addr = cur.execute("SELECT * FROM whales_ethereum;").fetchall() # get list of addresses info

    for row in addr:
        address = row[0]
        api = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&page=1&offset=1&sort=desc&apikey=xxxxxxxxxxxxxxxxxxxxxxxxx" #retrieve latest transaction for address w/ api key
        time.sleep(0.25) # time delay prevent api rate limit
        result = json.loads(requests.get(api).content)['result']
        hash_latest = result[0]['hash'] if result != "Error! Invalid address format" else context.bot.send_message(chat_id=context.job.context, text=f'Error in checking for {row[1]}')
        if (hash_latest != row[2] and result != "Error! Invalid address format"):
            txntype = "Incoming" if result[0]['from'] != address else "Outgoing"
            message += f"New {txntype} Transaction detected for {row[1]} {address}:\nhttps://etherscan.io/tx/{hash_latest}\n\n"
            cur.execute('UPDATE whales_ethereum SET txnhash=? WHERE Owner=?', (hash_latest, row[1])) # replace new transaction hash for address
            con.commit()

    con.close()

    if len(message) != 0: # prevent passing empty str to send_messages
        #context.bot.send_message(chat_id=context.job.context, text=message)
        requests.get(f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage?chat_id=@nicptetracker&text={message}')
    else:
        print('No new txns found this iteration!')

def stop(update,context): # func to stop the recursive checks
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=update.message.chat_id, text='Checking Stopped! Use "/start" to restart the tracker!')
    context.job_queue.stop()


#-------------------------- conversation handlers --------------------------#
NAME, ADDRESS = range(2)

def new(update: Update, context: CallbackContext):
    """Starts the conversation and ask whale name."""
    if update.message.chat_id != 433684446: # prevent other unautorised users
        context.bot.send_message(chat_id=update.message.chat_id, text='You are not authorised to use this bot!')
        return ConversationHandler.END
    else:
        update.message.reply_text(text='🔎 What is the name 📛 of the whale 🐳? 🔎')
        return NAME

def addwhalename(update: Update, context: CallbackContext): # func to add new whales to db
    """Continues to ask whale address."""
    con = sqlite3.connect('whale_list.db') # connect to db
    cur = con.cursor()
    cur.execute("INSERT INTO whales_ethereum VALUES (?,?,?)", ("nil", update.message.text,"new"))
    con.commit()
    con.close()
    update.message.reply_text(text='🔎 What is the address 👛 of the whale 🐳? 🔎')
    return ADDRESS

def addwhaleaddr(update: Update, context: CallbackContext): # func to add new whales to db
    """Continues to ask whale address."""
    con = sqlite3.connect('whale_list.db') # connect to db
    cur = con.cursor()
    cur.execute("UPDATE whales_ethereum SET Address=? WHERE txnhash=?", (update.message.text,"new"))
    con.commit()
    con.close()
    update.message.reply_text('Addition to database successful!')
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    print("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Operation Cancelled!'
    )
    return ConversationHandler.END

new_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new)],
        states={
            NAME: [MessageHandler(Filters.text, addwhalename)],
            ADDRESS: [MessageHandler(Filters.text, addwhaleaddr)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

NAMEUPDATE, ADDRESSUPDATE = range(2)

def update(update,context): # func to update addresses to db
    if update.message.chat_id != 433684446: # prevent other unautorised users
        context.bot.send_message(chat_id=update.message.chat_id, text='You are not authorised to use this bot!')
        return ConversationHandler.END
    else:
        con = sqlite3.connect('whale_list.db') # connect to db
        cur = con.cursor()
        addr = [list(i) for i in cur.execute("SELECT owner FROM whales_ethereum;").fetchall()]
        con.close()
        update.message.reply_text(text='🔎 What is the name 📛 of the whale 🐳 you want to update address? 🔎',reply_markup=ReplyKeyboardMarkup(
                addr, one_time_keyboard=True, input_field_placeholder='Name of Whale'))
        return NAMEUPDATE

def updatename(update,context): # func to delete whales from db
    name = update.message.text
    con = sqlite3.connect('whale_list.db') # connect to db
    cur = con.cursor()
    cur.execute("UPDATE whales_ethereum SET txnhash=? WHERE Owner=?", ("update",name))
    con.commit()
    con.close()
    update.message.reply_text(text='Insert new address 👛 for the the whale 🐳')
    return ADDRESSUPDATE

def updateaddress(update,context):
    addr = update.message.text
    con = sqlite3.connect('whale_list.db') # connect to db
    cur = con.cursor()
    cur.execute("UPDATE whales_ethereum SET Address=? WHERE txnhash=?", (addr,"update"))
    con.commit()
    con.close()
    update.message.reply_text('Database successfully updated!')
    return ConversationHandler.END
    
update_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('update', update)],
        states={
            NAMEUPDATE: [MessageHandler(Filters.text, updatename)],
            ADDRESSUPDATE: [MessageHandler(Filters.text, updateaddress)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

NAMEDELETE, ADDRESSDELETE = range(2)

def delete(update,context): # func to update addresses to db
    if update.message.chat_id != 433684446: # prevent other unautorised users
        context.bot.send_message(chat_id=update.message.chat_id, text='You are not authorised to use this bot!')
        return ConversationHandler.END
    else:
        con = sqlite3.connect('whale_list.db') # connect to db
        cur = con.cursor()
        addr = [list(i) for i in cur.execute("SELECT owner FROM whales_ethereum;").fetchall()]
        con.close()
        update.message.reply_text(text='🔎 What is the name 📛 of the whale 🐳 you want to delete? 🔎',
        reply_markup=ReplyKeyboardMarkup(
                addr, one_time_keyboard=True, input_field_placeholder='Name of Whale'))
        return NAMEDELETE

def deletename(update,context): # func to delete whales from db
    name = update.message.text
    con = sqlite3.connect('whale_list.db') # connect to db
    cur = con.cursor()
    cur.execute("UPDATE whales_ethereum SET txnhash=? WHERE Owner=?", ("delete",name))
    con.commit()
    con.close()
    update.message.reply_text(text='❌ Confirm delete? ❌', reply_markup=ReplyKeyboardMarkup(
            [['YES'],['NO']], one_time_keyboard=True))
    return ADDRESSDELETE

def deleteconfirm(update,context):
    option = update.message.text
    if option == "YES":
        con = sqlite3.connect('whale_list.db') # connect to db
        cur = con.cursor()
        cur.execute("DELETE FROM whales_ethereum WHERE txnhash=?", ("delete",))
        con.commit()
        con.close()
        update.message.reply_text('Address deleted successfully!')
    return ConversationHandler.END
    
delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete)],
        states={
            NAMEDELETE: [MessageHandler(Filters.text, deletename)],
            ADDRESSDELETE: [MessageHandler(Filters.text, deleteconfirm)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )



dispatcher.add_handler(CommandHandler('start', start)) # /start to initiate tracker
dispatcher.add_handler(CommandHandler('stop', stop)) # /stop to stop tracker
dispatcher.add_handler(new_conv_handler)
dispatcher.add_handler(update_conv_handler)
dispatcher.add_handler(delete_conv_handler)
updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=telegram_bot_token,
                          webhook_url='https://explorer-whale-tracker.herokuapp.com/' + telegram_bot_token)
#updater.bot.setWebhook('https://explorer-whale-tracker.herokuapp.com/' + telegram_bot_token)
updater.idle()
