import telebot
import requests
import json
import time
from datetime import datetime, timedelta

# -------------- VisioBox Database Segment START --------------

def req(url_request, token):
    url = url_request
    headers = {"Authorization": "OAuth {}".format(token)}

    response = requests.get(url, headers=headers)
    response_json = response.json()
    return response_json

def bool2text(boolean):
    if boolean:
        return 'Вкл.'
    else:
        return 'Выкл.'

with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)

#main function
def get_fresh_data(list_type):
    token_url = 'https://visiobox.cloud/v3/authenticate'
    token_payload= {"email":config["email"],"password":config["password"],"duration":180}
    token_headers = {}

    token_request = requests.post(token_url, data=json.dumps(token_payload), headers=token_headers)
    print(token_request.content)
    token_json = token_request.json()
    token = token_json['access_token']

    players = req('https://visiobox.cloud/v3/players?limit=100', token)

    vb_link = 'https://visiobox.cloud/#!players/single/{}/detail/'
    
    #online

    export_list_s_on = []

    for player in players['objects']:
        if player['devices'][0]['online']: #if device online
            export_1_s = '[{}]({})'.format(player['name'], vb_link.format(player['id']))
            export_3_s = '| Экр. {} '.format(bool2text(player['devices'][0]['power'])) # TV state
            export_final_s = export_1_s + ' ' + export_3_s
            export_list_s_on.append(export_final_s)

    export_list_s_on.sort()
    
    #offline

    export_list_s_off = []
    emoji = ''

    for player in players['objects']:
        if (player['devices'][0]['online'] == False): # if device offline
            device_name = '[{}]({})'.format(player['name'], vb_link.format(player['id']))
            emoji  = '🔴'
            export_final_s = device_name + ' ' + emoji
            export_list_s_off.append(export_final_s)
        if (player['devices'][0]['online'] == True) and (player['devices'][0]['power'] == False): #if device online and tv is off
            device_name = '[{}]({})'.format(player['name'], vb_link.format(player['id']))
            emoji = '🖥'
            export_final_s = device_name + ' ' + emoji 
            export_list_s_off.append(export_final_s)

    export_list_s_off.sort()

    #address

    export_list_address = []

    for player in players['objects']:
        device_linkname = '[{}]({}) '.format(player['name'], vb_link.format(player['id']))
        if player['devices'][0]['online']: #if device online
            emoji = '🔵'
        if (player['devices'][0]['online'] == False): # if device offline
            emoji = '🔴'
        if (player['devices'][0]['online'] == True) and (player['devices'][0]['power'] == False): #if device online and tv is off
            emoji = '🖥'
        adress = '\n{}\n'.format(player['user_data']['address']) # TV state
        export = device_linkname + emoji + adress
        export_list_address.append(export)

    export_list_address.sort()

    #sync

    export_list_sync = []

    for player in players['objects']:
        name = player['name']
        _sync_time_raw = datetime.strptime(player['devices'][0]['synchronized_at'], '%Y-%m-%dT%H:%M:%S.%f')
        _sync_time_MSK = _sync_time_raw + timedelta(hours=3)
        sync_time = datetime.strftime(_sync_time_MSK, '%T %d-%m-%Y')
        _time_now = datetime.now()
        if _time_now - _sync_time_MSK > timedelta(days = 1):
            xpt_line = '{} | {}'.format(name, sync_time)
            export_list_sync.append(xpt_line)

    export_list_sync.sort()

    #ammount

    ammount = len(players['objects'])

    if list_type == 'on':
        return export_list_s_on, ammount
    elif list_type == 'off':
        return export_list_s_off, ammount
    elif list_type == 'address':
        return export_list_address, None
    elif list_type == 'sync':
        return export_list_sync, ammount

# -------------- VisioBox Database Segment END --------------

# -------------- Telegram Bot Segment Start --------------

bot = telebot.TeleBot(config["telebot_token"])

keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,row_width=2)
keyboard.row('Включенные!', 'Выключенные!')
keyboard.row('Адреса!', 'Обновления!')

auth_user_list = config["user_list"]

def pm_send_message(msg, datatype, markdown_type):
    try:
        device_list, ammount = get_fresh_data(datatype)
        try:
            for item in device_list:
                if item == device_list[0]:
                    output_message = item
                    i = 1
                else:
                    output_message = output_message + '\n' + item
                    i = i + 1
                    if len(output_message) > 4800:
                            bot.send_message(msg.chat.id, output_message, parse_mode=markdown_type)
                            output_message = ''
            bot.send_message(msg.chat.id, output_message, parse_mode=markdown_type)
            if ammount != None: 
                bot.send_message(msg.chat.id, '{}/{}'.format(i,ammount))
        except Exception as e:
            bot.send_message(msg.chat.id, 'Sending message caused error:\n{}'.format(e))
    except Exception as e:
        bot.send_message(msg.chat.id, 'Device list error:\n{}'.format(e))
    

@bot.message_handler(content_types=['text'])
def status_message(message):
    if message.from_user.username in auth_user_list:
        if message.text == '/status':
            bot.send_message(message.chat.id, "Какие устройства показать?", reply_markup=keyboard)
        
        elif message.text == "/chat_id":
            bot.send_message(message.chat.id, message.chat.id)

        elif message.text == "Включенные!":
            pm_send_message(message, 'on', 'Markdown')
        elif message.text == "Выключенные!":
            pm_send_message(message, 'off', 'Markdown')
        elif message.text == "Адреса!":
            pm_send_message(message, 'address', 'Markdown')
        elif message.text == "Обновления!":
            pm_send_message(message, 'sync', None)
    else:
        bot.send_message(message.chat.id, "You are not authorized!")

# -------------- Telegram Bot Segment End --------------

print('Bot started!')

bot.infinity_polling(True)
'''
while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(e)
        time.sleep(15)
'''