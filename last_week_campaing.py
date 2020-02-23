import telebot
import requests
import json
import time
from datetime import datetime, timedelta

# -------------- VisioBox Database Segment START --------------

with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)

def req(url_request, token):
    url = url_request
    headers = {"Authorization": "OAuth {}".format(token)}

    response = requests.get(url, headers=headers)
    response_json = response.json()
    return response_json

campaign_link = 'https://visiobox.cloud/#!campaigns/{}/detail/'
campaign_list = ['Кампании, заканчивающиеся в течение 10 дней:']

#main function
def get_fresh_data():
    token_url = 'https://visiobox.cloud/v3/authenticate'
    token_payload= {"email":config["email"],"password":config["password"],"duration":60}
    token_headers = {}

    token_request = requests.post(token_url, data=json.dumps(token_payload), headers=token_headers)
    token_json = token_request.json()
    token = token_json['access_token']

    campaigns = req('https://visiobox.cloud/v3/od/campaigns/?type=normal&type=pipeline&exchange=0&limit=200', token)

    for campaign in campaigns['objects']:
        campaign_id = campaign['ad_campaign']['id']
        campaign_name = campaign['ad_campaign']['name']
        description = campaign['ad_campaign']['description']
        _date_end_raw = datetime.strptime(campaign['ad_campaign']['revision']['end'], '%Y-%m-%d')
        date = datetime.strftime(_date_end_raw ,'%d/%m/%Y')

        if campaign['ad_campaign']['state'] == 'running':
            if datetime.now() + timedelta(days=10) > _date_end_raw:
                if description != '':
                    output = '[{}]({}) {}\n┕ \[{}]'.format(campaign_name, campaign_link.format(campaign_id), date, description)
                else:
                    output = '[{}]({}) {}'.format(campaign_name, campaign_link.format(campaign_id), date)
                campaign_list.append(output)
    
    if len(campaign_list) > 1:
        return campaign_list
    else:
        return 0

#bot
bot = telebot.TeleBot(config["telebot_token"])

def pm_send_message(chat_id, markdown_type):
    try:
        device_list = get_fresh_data()
        if device_list != 0:
            try:
                for item in device_list:
                    if item == device_list[0]:
                        output_message = item
                        i = 1
                    else:
                        output_message = output_message + '\n' + item
                        i = i + 1
                        if len(output_message) > 4800:
                                bot.send_message(chat_id, output_message, parse_mode=markdown_type)
                                output_message = ''
                bot.send_message(chat_id, output_message, parse_mode=markdown_type)
            except Exception as e:
                bot.send_message(chat_id, 'Sending message caused error:\n{}'.format(e))
        else:
            pass
    except Exception as e:
        bot.send_message(chat_id, 'Device list error:\n{}'.format(e))

pm_send_message(config["work_chat"], 'Markdown')