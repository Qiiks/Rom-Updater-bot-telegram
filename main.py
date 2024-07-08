import telebot
from telebot import types
import json
import datetime
import requests
import time
import logging

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage

API_KEY = "Your API Key"
bot = telebot.TeleBot(API_KEY)
allowed_ids_file = "allowed_ids.json"
allowed_devs_file = "allowed_devs.json"

user_last_update_time = {}
# Function to calculate cooldown time
cooldown_seconds = 60

#setting variables
user_data = {}
data = {}
CHANNEL_ID = "ADMIN CHANNEL ID HERE"
POST_CHANNEL = "POSTING CHANNEL ID HERE"

logging.basicConfig(
    filename='app.log',  # Log file name
    filemode='a',  # Append mode
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log message format
)
def main():
    logging.info("Running Telebot")
    try:
        with open(allowed_ids_file, "r") as f:
            allowed_ids = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        allowed_ids = []

    try:
        with open(allowed_devs_file, "r") as f:
            allowed_devs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        allowed_devs = []

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        data_entry = db.table("call_backs").get(track.message_id == call.message.message_id)
        if not data_entry:
            return

        data = data_entry['data_t']
        data_sum = data_entry['data_summ']  # Assuming data is stored
        user_id = data_entry['userf']
        message_id = call.message.message_id

        if call.data == 'yes':
            tracking = {'name': [data['name']], 'banner': [data['banner']], 'message_ids': []}
            bot.edit_message_reply_markup(CHANNEL_ID, message_id, reply_markup=None)
            bot.send_message(user_id, "Update post has been approved!")
            bot.send_message(CHANNEL_ID, "Update approved!")
            if is_image_url(data['banner']):
                published = bot.send_photo(POST_CHANNEL, data['banner'], caption=data_sum, parse_mode='Markdown')
            else:
                with open(f"banners/{data['banner']}", 'rb') as photo:
                    published = bot.send_photo(POST_CHANNEL, photo, caption=data_sum, parse_mode='Markdown')
            tracking['message_ids'].append(published.message_id)
            save_to_json(data, user_id, published.message_id)
            print(tracking)
        elif call.data == 'no':
            bot.edit_message_reply_markup(CHANNEL_ID, message_id, reply_markup=None)
            bot.send_message(CHANNEL_ID, "Update denied!")
            bot.send_message(user_id, "Update post has been denied!")
        
        delete_callback_data(message_id)

    def delete_callback_data(message_id):
        caller = db.table("call_backs")
        caller.remove(track.message_id == message_id)

    def is_image_url(url):
        try:
            response = requests.head(url, allow_redirects=True)
            content_type = response.headers.get('content-type')
            return content_type and content_type.startswith('image/gif')
        except requests.RequestException:
            return False


    @bot.message_handler(commands=["help", "hello", "start"])
    def send_help_message(msg):
        try:
            print(msg.from_user)
            with open(allowed_ids_file, "r") as f:
                allowed_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_ids = []

        try:
            with open(allowed_devs_file, "r") as f:
                allowed_devs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_devs = []
        if msg.from_user.id in allowed_devs or msg.from_user.id in allowed_ids:
            print(msg.from_user.first_name, "used /start")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            btn1 = types.KeyboardButton("/update")
            btn4 = types.KeyboardButton("/add_admin")
            btn3 = types.KeyboardButton("/add_dev")
            btn2 = types.KeyboardButton("/close")
            markup.add(btn1, btn3, btn4, btn2)
            bot.send_message(msg.chat.id, "What do you want to do?", reply_markup=markup)
        else:
            bot.reply_to(msg, "You are not authorized to use this command.")

    def get_user_info(user_id):
        try:
            user = bot.get_chat(user_id)
            username = user.username
            first_name = user.first_name
            return username, first_name
        except telebot.apihelper.ApiException as e:
            print(f"Error: {e}")
            return None, None

    @bot.message_handler(commands=["close"])
    def send_help_message(msg):
        try:
            with open(allowed_ids_file, "r") as f:
                allowed_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_ids = []

        try:
            with open(allowed_devs_file, "r") as f:
                allowed_devs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_devs = []
        if msg.from_user.id in allowed_devs or msg.from_user.id in allowed_ids:
            markup = types.ReplyKeyboardRemove(selective=False)
            bot.send_message(msg.chat.id, "Good Bye!~", reply_markup=markup)


    @bot.message_handler(commands=["add_admin"])
    def add_admin_command(msg):
        try:
            with open(allowed_ids_file, "r") as f:
                allowed_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_ids = []

        try:
            with open(allowed_devs_file, "r") as f:
                allowed_devs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_devs = []
        if msg.from_user.id in allowed_ids:
            print(msg.from_user.first_name, "is using the bot")
            args = msg.text.split()[1:]  # Remove the '/add_admin' part
            if args:
                try:
                    new_id = int(args[0])
                    if new_id not in allowed_ids:
                        allowed_ids.append(new_id)
                        with open(allowed_ids_file, "w") as f:
                            json.dump(allowed_ids, f)
                        bot.reply_to(msg, f"Added user ID {new_id} as an admin.")
                    else:
                        bot.reply_to(msg, f"User ID {new_id} is already an admin.")
                except ValueError:
                    bot.reply_to(msg, "Invalid user ID.")
            else:
                bot.reply_to(msg, "Usage: /add_admin <user_id>")
        else:
            bot.reply_to(msg, "You are not authorized to use this command.")


    def get_valid_date(prompt):
            try:
                # Try to parse the input to a date object
                date_obj = datetime.datetime.strptime(prompt, '%Y-%m-%d')
                return True
            except ValueError:
                return False


    @bot.message_handler(commands=["add_dev"])
    def add_dev_command(msg):
        try:
            with open(allowed_ids_file, "r") as f:
                allowed_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_ids = []

        try:
            with open(allowed_devs_file, "r") as f:
                allowed_devs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_devs = []
        if msg.from_user.id in allowed_ids:
            print(msg.from_user.first_name, "is using the bot")
            args = msg.text.split()[1:]  # Remove the '/add_dev' part
            if args:
                try:
                    new_id = int(args[0])
                    if new_id not in allowed_devs:
                        allowed_devs.append(new_id)
                        with open(allowed_devs_file, "w") as f:
                            json.dump(allowed_devs, f)
                        bot.reply_to(msg, f"Added user ID {new_id} as a developer.")
                    else:
                        bot.reply_to(msg, f"User ID {new_id} is already a developer.")
                except ValueError:
                    bot.reply_to(msg, "Invalid user ID.")
            else:
                bot.reply_to(msg, "Usage: /add_dev <user_id>")
        else:
            bot.reply_to(msg, "You are not authorized to use this command.")


    # Database Management -----------------------------------------------------------------------------------
    db = TinyDB('db.json', storage=JSONStorage, indent=6)
    track = Query()
    track_user = db.table('Tracking')
    rom_info = db.table("rom_info")
    caller = db.table("call_backs")

    def save_to_json(data, user_id, tracking):
    # Get the user tracking information
        searched = track_user.get(track.userid == user_id)
        # Get the ROM info
        info = rom_info.get(track.name == data['name'])

        if info:
            device_i = info.get('device_c', [])
            # Ensure unique devices are added
            for device in data['device']:
                if device not in device_i:
                    device_i.append(device)
            rom_info.update({'device_c': device_i}, track.name == data['name'])
        else:
            rom_info.insert({
                "name": data["name"],
                "banner": data["banner"]
            })

        if searched:
            codename = searched.get('devices_c', [])
            romss = searched.get('roms', [])
            banners = searched.get('banners', [])
            msgidss = searched.get('msgids', [])
            devicess = searched.get('devices', [])

            # Update devices and device names
            for device_name in data['device_name']:
                if device_name not in devicess:
                    devicess.append(device_name)
            track_user.update({'devices': devicess}, track.userid == user_id)

            # Update message IDs
            if tracking not in msgidss:
                msgidss.append(tracking)
            track_user.update({'msgids': msgidss}, track.userid == user_id)

            # Update banners
            if data['banner'] not in banners:
                banners.append(data['banner'])
            track_user.update({'banners': banners}, track.userid == user_id)

            # Update device codes
            for device in data['device']:
                if device not in codename:
                    codename.append(device)
            track_user.update({'devices_c': codename}, track.userid == user_id)

            # Update ROMs
            if data['name'] not in romss:
                romss.append(data['name'])
            track_user.update({'roms': romss}, track.userid == user_id)
        else:
            # Insert new tracking information for the user
            track_user.insert({
                "userid": user_id,
                "roms": [data['name']],
                "banners": [data['banner']],
                "devices_c": data['device'],
                "devices": data['device_name'],
                "msgids": [tracking]
            })

    #--------------------------------------------------------------------------------------------------------------------

    @bot.message_handler(commands=["add_banner"])
    def banner_assign(msg):
        try:
            with open(allowed_ids_file, "r") as f:
                allowed_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_ids = []
        
        if msg.from_user.id in allowed_ids:
            message = bot.reply_to(msg, "Which rom do you want to assign banner to?")
            bot.register_next_step_handler(message, assigner)
    rom_tex = {"name": ""}
    def assigner(msg):
        rom_tex["name"] = msg.text
        try:
            info = rom_info.get(track.name == msg.text)
            if info:
                bann = info.get('banner')
                bot.send_message(msg.chat.id, "The rom already has the following banner assigned to it:")
                if is_image_url(bann):
                    bot.send_photo(msg.chat.id, bann, parse_mode='Markdown')
                else:
                    with open(f"banners/{bann}", 'rb') as photo:
                        bot.send_photo(msg.chat.id, photo, parse_mode='Markdown')
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, f"Do you wish to assign a new banner to it?", reply_markup=markup)
                msg = bot.register_next_step_handler(message, chcekr)
            else:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, f"The rom {msg.text} is not in our database. Do you wish to create an entry and assign a banner to it?", reply_markup=markup)
                msg = bot.register_next_step_handler(message, chcekr)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error Occured: {e}")
    def chcekr(msg):
        if msg.text.lower() == "yes":
            bot.send_message(msg.chat.id, "Please send the banner image or image link for the ROM update.")
            bot.register_next_step_handler(msg, assignment)
        if msg.text.lower() == "no":
            bot.send_message(msg.chat.id, "Banner assign process cancelled.")
            return        
    def assignment(msg):
        try:
            rom_n = rom_tex["name"]
            info = rom_info.get(track.name == rom_n)
            if msg.content_type == 'text': 
                if msg.text.lower() == '/cancel':
                    cancel_update(msg)
                    return
            if msg.content_type == 'photo':
                file_info = bot.get_file(msg.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(f'banners/banner_{rom_n}.jpg', 'wb') as new_file:
                    new_file.write(downloaded_file)
                bannrr = f'banner_{rom_n}.jpg'
                if info:
                        bann= info.get('banner')
                        rom_info.update({'banner': bannrr}, track.name == rom_n)
                        bot.send_message(msg.chat.id, "The banner has been successfully updated.")
                        rom_tex.clear()
                else:
                    bann= info.get('banner')
                    rom_info.insert({
                                        "name": rom_n,
                                        "banner": bannrr
                                    })
                    rom_tex.clear()

            elif msg.content_type == 'text' and msg.text.startswith('http'):
                if is_image_url(msg.text):
                    
                    if info:
                        bann= info.get('banner')
                        rom_info.update({'banner': msg.text}, track.name == rom_n)
                        bot.send_message(msg.chat.id, "The banner has been successfully updated.")
                        rom_tex.clear()
                    else:
                        bann= info.get('banner')
                        rom_info.insert({
                                            "name": rom_n,
                                            "banner": bannrr
                                        })
                        rom_tex.clear()
                else:
                    message = bot.reply_to(msg, "Please send a valid image link.")
                    bot.register_next_step_handler(message, assignment)
                    return
            else:
                message = bot.reply_to(msg, "Please send a valid image or image link.")
                bot.register_next_step_handler(message, assignment)
                return
        except FileNotFoundError:
            bot.reply_to(msg, "Banner image not found.")
        except Exception as e:
            bot.reply_to(msg, f"Error sending photo: {e}")

    @bot.message_handler(commands=['update'])
    def main_update(msg):
        user_id = msg.from_user.id
        
        if user_id in user_last_update_time:
            last_update_time = user_last_update_time[user_id]
            current_time = time.time()
            time_since_last_update = current_time - last_update_time
            
            if time_since_last_update < cooldown_seconds:
                remaining_cooldown = cooldown_seconds - int(time_since_last_update)
                bot.reply_to(msg, f"You can only run /update once every {cooldown_seconds} seconds. Please wait {remaining_cooldown} seconds before trying again.")
                return
        
        user_last_update_time[user_id] = time.time()
        
        try:
            with open(allowed_ids_file, "r") as f:
                allowed_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_ids = []

        try:
            with open(allowed_devs_file, "r") as f:
                allowed_devs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            allowed_devs = []

        if msg.from_user.id in allowed_devs or msg.from_user.id in allowed_ids:
            print(msg.from_user.first_name, "is using /update command")
            start_update(msg)
        else:
            bot.send_message(msg.chat.id, "You are not authorized to use this bot.")

    def start_update(msg):
        user_data[msg.chat.id] = {'step': 'start'}
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
        markup.add('Yes', 'No')
        message = bot.reply_to(msg, "Please respond with 'Yes' or 'No'. You can type /cancel at any step if you wish to cancel the rom annoucement request. Additionally you can do /back at any step to go back to the previous question in the case of a misinput", reply_markup=markup)
        bot.register_next_step_handler(message, process_confirmation)

    def process_confirmation(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            start_update(msg)
            return
        if msg.text.lower() == 'yes':
            user_data[msg.chat.id]['step'] = 'process_rom_name'
            searched = track_user.get(track.userid == msg.from_user.id)
            #print(searched) 
            if searched:
                roms = searched.get('roms', [])
                #print(roms)
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for i in roms:
                    #print(i)
                    markup.add(i)
                message = bot.reply_to(msg, "You have posted before, select one of the mentioned roms from your previous posts, or type the name of a new rom.", reply_markup= markup)
                bot.register_next_step_handler(message, process_rom_name)
            else:
                message = bot.reply_to(msg, "What's the name of your rom?", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, process_rom_name)
        elif msg.text.lower() == 'no':
            bot.reply_to(msg, "Update process canceled.",reply_markup=types.ReplyKeyboardRemove())
        else:
            message = bot.reply_to(msg, "Please respond with 'Yes' or 'No'. You can type /cancel at any step if you wish to cancel the rom annoucement request. Additionally you can do /back at any step to go back to the previous question in the case of a misinput" )
            bot.register_next_step_handler(message, process_confirmation)

    def process_rom_name(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question, reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['name'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_image'
        searched = track_user.get(track.userid == msg.from_user.id)
        if searched:
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_rom_name,
                'question': "You have posted before, select one of the mentioned roms from your previous posts, or type the name of a new rom."
            }
        else:
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_rom_name,
                'question': "What's the name of your rom?"
            }
        if rom_info.get(track.name == user_data[msg.chat.id]['name']):
            message = bot.reply_to(msg, "This ROM is already in the database. We have an banner image available for this rom.")
            info = rom_info.get(track.name == user_data[msg.chat.id]['name'])
            user_data[msg.chat.id]['banner'] = info.get('banner')
            user_data[msg.chat.id]['step'] = 'process_rom_officiality'
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('Official', 'Unofficial')
            message = bot.reply_to(msg, "Is the ROM an Official Build or Unofficial build", reply_markup=markup)
            bot.register_next_step_handler(message, process_rom_officiality)
            return
        else:
            message = bot.reply_to(msg, "Please send the banner image or image link for the ROM update.", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_image)

    def process_image(msg):
        if msg.content_type == "text":
            if msg.text.lower() == '/cancel':
                cancel_update(msg)
                return
            if msg.text.lower() == "/back":
                previous_step = user_data[msg.chat.id].get('previous_step')
                if previous_step:
                    previous_step_function = previous_step['function']
                    previous_step_question = previous_step['question']
                    searched = track_user.get(track.userid == msg.from_user.id)
                if searched:
                    roms = searched.get('roms', [])
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
                    for i in roms:
                        markup.add(i)
                    message = bot.reply_to(msg, previous_step_question, reply_markup=markup)
                    bot.register_next_step_handler(message, previous_step_function)
                return
        if msg.content_type == 'photo':
            file_info = bot.get_file(msg.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(f'banners/banner_{user_data[msg.chat.id]['name']}.jpg', 'wb') as new_file:
                new_file.write(downloaded_file)
            user_data[msg.chat.id]['banner'] = f'banner_{user_data[msg.chat.id]['name']}.jpg'
        elif msg.content_type == 'text' and msg.text.startswith('http'):
            if is_image_url(msg.text):
                user_data[msg.chat.id]['banner'] = msg.text
            else:
                message = bot.reply_to(msg, "Please send a valid image link.")
                bot.register_next_step_handler(message, process_image)
                return
        else:
            message = bot.reply_to(msg, "Please send a valid image or image link.")
            bot.register_next_step_handler(message, process_image)
            return

        user_data[msg.chat.id]['step'] = 'process_rom_officiality'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_image,
            'question': "Please send the banner image or image link for the ROM update."
        }
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Official', 'Unofficial')
        message = bot.reply_to(msg, "Is the ROM an Official Build or Unofficial build", reply_markup=markup)
        bot.register_next_step_handler(message, process_rom_officiality)

    def process_rom_officiality(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
            if previous_step_function == process_rom_name:
                searched = track_user.get(track.userid == msg.from_user.id)
                if searched:
                    roms = searched.get('roms', [])
                    markup11 = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
                    for i in roms:
                        markup11.add(i)
                    message = bot.send_message(msg.chat.id, previous_step_question, reply_markup=markup11)
                    bot.register_next_step_handler(message, previous_step_function)
            else: 
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        if msg.text.lower() == 'official':
            user_data[msg.chat.id]['officiality'] = 'Official'
        else:
            user_data[msg.chat.id]['officiality'] = 'Unofficial'
        user_data[msg.chat.id]['step'] = 'process_rom_version'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_rom_officiality,
            'question': "Is the ROM an Official Build or Unofficial build"
        }
        message = bot.reply_to(msg, "What's the version of the ROM? (Not Android Version)", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_rom_version)

    def process_rom_version(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('Official', 'Unofficial')
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question, reply_markup=markup)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['version'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_android_version'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_rom_version,
            'question': "What's the version of the ROM? (Not Android Version)"
        }
        message = bot.reply_to(msg, "What's the Android version?")
        bot.register_next_step_handler(message, process_android_version)

    def process_android_version(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['android_version'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_codename_adds'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_android_version,
            'question': "What's the Android version?"
        }
        #devicess = ["Oriole", "Raven", "Bluejay"]
        #markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        #for i in devicess:
        #    markup.add(i)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Yes', 'No')
        message = bot.reply_to(msg, "Do you wish to post for multiple devices? (Yes/No)", reply_markup=markup)
        bot.register_next_step_handler(message, process_codename_adds)



    def process_codename_adds(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        if msg.text.lower() == 'yes':
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_codename_adds,
                'question': "Do you wish to post for multiple devices? (Yes/No)"
            }
            devicess = ["Oriole", "Raven", "Bluejay"]
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for i in devicess:
                markup.add(i)
            user_data[msg.chat.id]['device'] = []
            message = bot.reply_to(msg, "Select the devices you wish to add and then press 'Done' once you have selected them", reply_markup=markup)
            bot.register_next_step_handler(message, process_rom_codenames)
        else:
            user_data[msg.chat.id]['device'] = [None]
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_codename_adds,
                'question': "Do you wish to post for multiple devices? (Yes/No)"
            }
            devicess = ["Oriole", "Raven", "Bluejay"]
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for i in devicess:
                markup.add(i)
            message = bot.reply_to(msg, "Select the device you wish to add the rom for.", reply_markup=markup)
            bot.register_next_step_handler(message, process_rom_codename)


    def process_rom_codenames(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, previous_step_question, reply_markup=markup)
                bot.register_next_step_handler(message, previous_step_function)
            return
        devicess = ["Oriole", "Raven", "Bluejay"]
        user_data[msg.chat.id]['step'] = 'process_rom_update_date'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_codename_adds,
            'question': "Do you wish to post for multiple devices? (Yes/No)"
        }
        devicess = ["Oriole", "Raven", "Bluejay"]
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for i in devicess:
            markup.add(i)
        markup.add("Done")
        devicess = ["Oriole", "Raven", "Bluejay"]
        if msg.text.lower() == 'done':
            message = bot.reply_to(msg, "What's the rom update date? (YYYY-MM-DD)")
            bot.register_next_step_handler(message, process_rom_update_date)
        if msg.text not in devicess:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for i in devicess:
                markup.add(i)
            message = bot.reply_to(msg, "Please select a valid device codename", reply_markup=markup)
            bot.register_next_step_handler(message, process_rom_codename)
            return
        message = bot.reply_to(msg, "Select your next device. Press 'Done' once your done selecting", reply_markup=markup)
        bot.register_next_step_handler(message, process_code_adder)
        user_data[msg.chat.id]['device'].append(msg.text)
    #print(user_data[msg.chat.id]['device'])
        return


    def process_code_adder(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_codename_adds,
            'question': "Do you wish to post for multiple devices or single? (Yes/No)"
        }
        devicess = ["Oriole", "Raven", "Bluejay"]
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        for i in devicess:
            markup.add(i)
        markup.add("Done")
        if msg.text.lower() == 'done':
            message = bot.reply_to(msg, "What's the rom update date? (YYYY-MM-DD)")
            bot.register_next_step_handler(message, process_rom_update_date)
            return
        if msg.text in user_data[msg.chat.id]['device']:
            message = bot.reply_to(msg, "You have already added this device.", reply_markup=markup)
            #(user_data[msg.chat.id]['device'])
            bot.register_next_step_handler(message, process_code_adder)
            return
        if msg.text not in user_data[msg.chat.id]['device']:
            user_data[msg.chat.id]['device'].append(msg.text)
            #print(user_data[msg.chat.id]['device'])
            message = bot.reply_to(msg, "Select your next device. Press 'Done' once your done selecting", reply_markup=markup)
            bot.register_next_step_handler(message, process_code_adder)
            return
        if msg.text not in devicess:
            message = bot.reply_to(msg, "Please select a valid device codename", reply_markup=markup)
            bot.register_next_step_handler(message, process_code_adder)
            return

    def process_rom_codename(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        devicess = ["Oriole", "Raven", "Bluejay"]
        user_data[msg.chat.id]['device'] = [msg.text]
        user_data[msg.chat.id]['step'] = 'process_rom_update_date'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_codename_adds,
            'question': "Do you wish to post for multiple devices or single? (Yes/No)"
        }
        if msg.text not in devicess:
            devicess = ["Oriole", "Raven", "Bluejay"]
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for i in devicess:
                markup.add(i)
            message = bot.reply_to(msg, "Please select a valid device codename", reply_markup=markup)
            bot.register_next_step_handler(message, process_rom_codename)
            return
        message = bot.reply_to(msg, "What's the rom update date? (YYYY-MM-DD)")
        bot.register_next_step_handler(message, process_rom_update_date)








    def process_rom_update_date(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                devicess = ["Oriole", "Raven", "Bluejay"]
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, previous_step_question, reply_markup=markup)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['date'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_spl_version'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_rom_update_date,
            'question': "What's the rom update date? (YYYY-MM-DD)"
        }
        if get_valid_date(msg.text):
            year, month, day = map(int, msg.text.split("-"))
            user_data[msg.chat.id]['year'] = year
            user_data[msg.chat.id]['month'] = month
            user_data[msg.chat.id]['day'] = day
            user_data[msg.chat.id]['date'] = msg.text
            message = bot.reply_to(msg, "What's the SPL?")
            bot.register_next_step_handler(message, process_spl_version)
        else:
            message = bot.reply_to(msg, "Please enter a valid date in the valid format")
            bot.register_next_step_handler(message, process_rom_update_date)
            return
        #message = bot.reply_to(msg, "Please enter a valid date")
        #bot.register_next_step_handler(message, process_rom_update_date)
        #return


    def process_spl_version(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        chek = msg.text[0].upper() + msg.text[1:].lower()
        user_data[msg.chat.id]['spl_version'] = chek
        user_data[msg.chat.id]['step'] = 'process_qpr'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_spl_version,
            'question': "What's the SPL?"
        }
        months = ['January', 'February', 'March', 'April', 'May', 'June','July', 'August','September', 'October', 'November', 'December' ]
        if chek not in months:
            message = bot.reply_to(msg, "Please enter a valid month")
            bot.register_next_step_handler(message, process_spl_version)
            return
        markup = types.ReplyKeyboardMarkup(row_width=2,one_time_keyboard=True)
        qprs = ["RC", "None", "QPR1", "QPR2", "QPR3"]
        for  i in qprs:
            markup.add(i)
        message = bot.reply_to(msg, "What's the QPR version?", reply_markup=markup)
        bot.register_next_step_handler(message, process_qpr)

    def process_qpr(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['qpr'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_changelog_link'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_qpr,
            'question': "What's the QPR version?"
        }
        qprs = ["RC", "None", "QPR1", "QPR2", "QPR3"]
        if msg.text not in qprs:
            markup = types.ReplyKeyboardMarkup(row_width=2,one_time_keyboard=True)
            for  i in qprs:
                markup.add(i)
            message = bot.reply_to(msg, "Please select a valid QPR version", reply_markup=markup)
            bot.register_next_step_handler(message, process_qpr)
            return
        message = bot.reply_to(msg, "Please provide the source changelog link.")
        bot.register_next_step_handler(message, process_changelog_link)

    def process_changelog_link(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['changelog_link'] = msg.text
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_changelog_link,
            'question': "Please provide the source changelog link."
        }
        message = bot.reply_to(msg, "Please provide rom changelog.")
        bot.register_next_step_handler(message, process_rom_changelog)

    def process_rom_changelog(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['changelog'] = msg.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Yes', 'No')
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_rom_changelog,
            'question': "Please provide the rom changelog"
        }
        message = bot.reply_to(msg, "Is there an installation guide available?", reply_markup=markup)
        bot.register_next_step_handler(message, process_installation_guide)

    def process_installation_guide(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        if msg.text.lower() == 'yes':
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_installation_guide,
                'question': "Is there an installation guide available?"
            }
            message = bot.reply_to(msg, "Please provide the installation guide link.", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_installation_guide_link)
        else:
            user_data[msg.chat.id]['installation_guide'] = None
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_installation_guide,
                'question': "Is there an installation guide available?"
            }
            message = bot.reply_to(msg, "What's the support group link?", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_support_group_link)

    def process_installation_guide_link(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['installation_guide'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_support_group_link'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_installation_guide_link,
            'question': "Please provide the installation guide link."
        }
        message = bot.reply_to(msg, "What's the support group link?", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_support_group_link)

    def process_support_group_link(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['support_group_link'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_device_name'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_support_group_link,
            'question': "What's the support group link?"
        }
        user_data[msg.chat.id]['download_link'] = []
        process_download_link(msg)

    def process_download_link(msg):
        chat_id = msg.chat.id
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[chat_id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        # Initialize download links if not already initialized
        if 'download_link' not in user_data[chat_id]:
            user_data[chat_id]['download_link'] = []
        # Check if there are more devices to process
        if 'device_index' not in user_data[chat_id]:
            user_data[chat_id]['device_index'] = 0
        device_index = user_data[chat_id]['device_index']
        devices = user_data[chat_id]['device']
        if device_index < len(devices):
            if device_index > 0:
                # Save the previous download link
                user_data[chat_id]['download_link'].append(msg.text)
            # Ask for the next device download link
            device_name = devices[device_index]
            user_data[chat_id]['previous_step'] = {
                'function': process_download_link,
                'question': f"Please provide the download link for {device_name}."
            }
            user_data[chat_id]['device_index'] += 1
            message = bot.reply_to(msg, f"Please provide the download link for {device_name}.")
            bot.register_next_step_handler(message, process_download_link)
            return
        else:
            # All download links collected, ask for additional notes
            user_data[chat_id]['download_link'].append(msg.text)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('Yes', 'No')
            message = bot.reply_to(msg, "Do you wish to add any additional notes? Such as donation links?", reply_markup=markup)
            bot.register_next_step_handler(message, process_additional)

    def process_additional(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        if msg.text.lower() == 'yes':
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_additional,
                'question': "Do you wish to add any additional notes? Such as donation links?"
            }
            message = bot.reply_to(msg, "Provide the additional notes you wish to add.", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_notes)
        else:
            user_data[msg.chat.id]['additional'] = None
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_additional,
                'question': "Do you wish to add any additional notes? Such as donation links?"
            }
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('Yes', 'No')
            message = bot.reply_to(msg, "Are you the maintainer?", reply_markup=markup)
            bot.register_next_step_handler(message, process_maintainer)


    def process_notes(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Yes', 'No')
                message = bot.reply_to(msg, previous_step_question, reply_markup=markup)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['additional'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_md5'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_notes,
            'question': "Provide the additional notes you wish to add."
        }
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Yes', 'No')
        message = bot.reply_to(msg, "Are you the maintainer?", reply_markup=markup)
        bot.register_next_step_handler(message, process_maintainer)


    def process_maintainer(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['step'] = 'process_md5'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_maintainer,
            'question': "Are you the maintainer"
        }
        if msg.text.lower() == 'yes':
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_maintainer,
                'question': "Are you the maintainer?"
            }
            if msg.from_user.username:
                user_data[msg.chat.id]['maintainer'] = msg.from_user.username
            else:
                user_data[msg.chat.id]['maintainer'] = msg.from_user.first_name
            user_data[msg.chat.id]['maintainer_id'] = msg.from_user.id
            message = bot.reply_to(msg, "Please provide the MD5 Checksum", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_md5)
        else:
            user_data[msg.chat.id]['previous_step'] = {
                'function': process_maintainer,
                'question': "Are you the maintainer?"
            }
            message = bot.reply_to(msg, "Please provide the username and ID in the following format (ignore the <>): <username> | <id>", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_maintainer_who)

    def process_maintainer_who(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['step'] = 'process_md5'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_maintainer,
            'question': "Please provide the username and ID in the following format (ignore the <>): <username> | <id>"
        }
        actual = msg.text.split(' | ')
        if len(actual)!= 2:
            message = bot.reply_to(msg, "Please provide the username and ID in the following format (ignore the <>): <username> | <id>")
            bot.register_next_step_handler(message, process_maintainer_who)
            return
        else:
            user_data[msg.chat.id]['maintainer'] = actual[0]
            user_data[msg.chat.id]['maintainer_id'] = actual[1]
            message = bot.reply_to(msg, "Please provide the MD5 checksum.", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_md5)

    def process_md5(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == '/back':
            previous_step = user_data[msg.chat.id].get('previous_step')
            if previous_step:
                previous_step_function = previous_step['function']
                previous_step_question = previous_step['question']
                message = bot.reply_to(msg, previous_step_question)
                bot.register_next_step_handler(message, previous_step_function)
            return
        user_data[msg.chat.id]['md5'] = msg.text
        user_data[msg.chat.id]['step'] = 'process_size'
        user_data[msg.chat.id]['previous_step'] = {
            'function': process_md5,
            'question': "Please provide the MD5 checksum."
        }
        finalize_update(msg)

    def finalize_update(msg):
        data = user_data[msg.chat.id]
        data['device_name'] = []
        data['device_nams'] = []
        for i in data['device']:
            match i.lower():
                case 'oriole':
                    data['device_name'].append('Pixel 6')
                case 'raven':
                    data['device_name'].append('Pixel 6 Pro')
                case 'bluejay':
                    data['device_name'].append('Pixel 6a')
                case _:
                    data['device_name'].append(data['device'])
        for i in data['device']:
            match i.lower():
                case 'oriole':
                    data['device_nams'].append('6')
                case 'raven':
                    data['device_nams'].append('6 Pro')
                case 'bluejay':
                    data['device_nams'].append('6a')
                case _:
                    data['device_nams'].append(data['device'])
        data['d'] = ""
        for i in data['device']:
            data['d'] += f"#{i} "
        data['dd'] = []
            #ata['dd'].append(data['device_nams'])
        data['dd'] = '/'.join(map(str, data['device_nams']))
        data['downs'] = []
        for i in range(len(data['device'])):
            data['downs'].append(f"[{data['device'][i]}]({data['download_link'][i]})")
        data['downs'] = ' | '.join(map(str, data['downs']))
        data_summary = (
                f"#{data['name']} #{data['officiality']} #A{data['android_version']} #ROM {data['d']}\n"
                f"*{data['name']}* *{data['version']}* - *{data['officiality'].upper()}* | *Android {data['android_version']} {data['qpr']}* | *{data['spl_version']} {data['year']} SPL*\n*Pixel {data['dd']}*\n"
                f"*Updated:* {data['date']}\n\n"
                #f"📦 Download: [{data['device']}]({data['download_link']})\n\n"
                f"📦 Download: {data['downs']}\n\n"
            )
        data_summary += (
                f"*Changelog:*\n{data['changelog']}\n\n"
                f"🔗 [Source Changelog]({data['changelog_link']})\n\n"
                f"*Notes:* \n")
        if data['installation_guide']:
                data_summary += f"📖 [Guide]({data['installation_guide']})\n"
        data_summary += f"Join Rom [Support Channel]({data['support_group_link']})\n"
        if data['additional']:
            data_summary += (f"{data['additional']}\n")
        data_summary += (
                f"\n*By* [@{data['maintainer']}](tg://user?id={str(data['maintainer_id'])})\n"
                f"*Follow* @Pixel6Updates\n"
                f"*Join* @Pixel6Chat"
            )
        bot.send_message(msg.chat.id, "Please confirm the details:")
        try:
            if is_image_url(data['banner']):
                bot.send_photo(msg.chat.id, data['banner'], caption=data_summary, parse_mode='Markdown')
            else:
                with open(f"banners/{data['banner']}", 'rb') as photo:
                    bot.send_photo(msg.chat.id, photo, caption=data_summary, parse_mode='Markdown')
        except FileNotFoundError:
            bot.reply_to(msg, "Banner image not found.")
        except Exception as e:
            bot.reply_to(msg, f"Error sending photo: {e}")

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Yes', 'No')
        message = bot.send_message(msg.chat.id, "Is the information correct?", reply_markup=markup)
        bot.register_next_step_handler(message, process_final_confirmation)

    def process_final_confirmation(msg):
        if msg.text.lower() == '/cancel':
            cancel_update(msg)
            return
        if msg.text.lower() == 'yes':
            data = user_data[msg.chat.id]
            
            data_summary = (
                f"#{data['name']} #{data['officiality']} #A{data['android_version']} #ROM {data['d']}\n"
                f"*{data['name']}* *{data['version']}* - *{data['officiality'].upper()}* | *Android {data['android_version']} {data['qpr']}* | *{data['spl_version']} {data['year']} SPL*\n*Pixel {data['dd']}*\n"
                f"*Updated:* {data['date']}\n\n"
                #f"📦 Download: [{data['device']}]({data['download_link']})\n\n"
                f"📦 Download: {data['downs']}\n\n"
            )
            data_summary += (
                    f"*Changelog:*\n{data['changelog']}\n\n"
                    f"🔗 [Source Changelog]({data['changelog_link']})\n\n"
                    f"*Notes:* \n")
            if data['installation_guide']:
                    data_summary += f"📖 [Guide]({data['installation_guide']})\n"
            data_summary += f"Join Rom [Support Channel]({data['support_group_link']})\n"
            if data['additional']:
                data_summary += (f"{data['additional']}\n")
            data_summary += (
                    f"\n*By* [@{data['maintainer']}](tg://user?id={str(data['maintainer_id'])})\n"
                    f"*Follow* @Pixel6Updates\n"
                    f"*Join* @Pixel6Chat"
                )
            admins_confirm = types.InlineKeyboardMarkup()
            admins_confirm.add(types.InlineKeyboardButton(text="Approve?", callback_data="yes"))
            admins_confirm.add(types.InlineKeyboardButton(text="Deny", callback_data="no"))
            del data['previous_step']
            try:
                if is_image_url(data['banner']):
                    confirmer = bot.send_photo(CHANNEL_ID, data['banner'], caption=data_summary, parse_mode='Markdown', reply_markup=admins_confirm)
                    caller.insert({'message_id': confirmer.message_id, 'userf': msg.from_user.id, 'data_summ': data_summary, 'data_t': data})
                    bot.send_message(CHANNEL_ID, f"The following is the checksum to verify the rom:\n```{data['md5']}", parse_mode='MarkdownV2')
                else:
                    with open(f"banners/{data['banner']}", 'rb') as photo:
                        confirmer = bot.send_photo(CHANNEL_ID, photo, caption=data_summary, parse_mode='Markdown', reply_markup=admins_confirm)
                        #print(data)
                        caller.insert({'message_id': confirmer.message_id, 'userf': msg.from_user.id, 'data_summ': data_summary, 'data_t': data})
                        bot.send_message(CHANNEL_ID, f"The following is the checksum to verify the rom:\n```{data['md5']}```", parse_mode='MarkdownV2')
                @bot.callback_query_handler(func=lambda call: True)
                def handle_admin_approval(call):
                    if call.data == 'yes':
                            tracking = {'name': [data['name']], 'banner': [data['banner']], 'message_ids': []}
                            bot.edit_message_reply_markup(CHANNEL_ID, confirmer.message_id, reply_markup=None)
                            bot.send_message(msg.chat.id, "Update post has been approved!")
                            bot.send_message(CHANNEL_ID, "Update approved!")
                            if is_image_url(data['banner']):
                                published = bot.send_photo(POST_CHANNEL, data['banner'], caption=data_summary, parse_mode='Markdown')
                            else:
                                with open(f"banners/{data['banner']}", 'rb') as photo:
                                    published = bot.send_photo(POST_CHANNEL, photo, caption=data_summary, parse_mode='Markdown')
                            tracking['message_ids'].append(published.message_id)
                            save_to_json(data, msg.from_user.id, published.message_id)
                            delete_callback_data(confirmer.message_id)
                            #print(tracking)
                        #except Exception as e:
                            #bot.reply_to(call.message, f"Error approving update: {e}")
                    elif call.data == 'no':
                        bot.edit_message_reply_markup(CHANNEL_ID, confirmer.message_id, reply_markup=None)
                        bot.send_message(CHANNEL_ID, "Update denied!")
                        bot.send_message(msg.chat.id, "Update post has been denied!")
                        delete_callback_data(confirmer.message_id)
                
            except FileNotFoundError:
                bot.reply_to(msg, "Banner image not found.")
            except Exception as e:
                bot.reply_to(msg, f"Error sending photo to channel: {e}")
                user_data.pop(msg.chat.id)
                data.clear()
                return

            bot.send_message(msg.chat.id, "ROM update has been saved and uploaded successfully!", reply_markup=types.ReplyKeyboardRemove())
            user_data.pop(msg.chat.id)
            data.clear()
        else:
            bot.reply_to(msg, "Update process canceled.", reply_markup=types.ReplyKeyboardRemove())
            user_data.pop(msg.chat.id)
            data.clear()

    @bot.message_handler(commands=["cancel"])
    def cancel_update(msg):
        if msg.chat.id in user_data:
            data.clear()
            user_data.pop(msg.chat.id)
        bot.send_message(msg.chat.id, "Update process canceled.", reply_markup=types.ReplyKeyboardRemove())
    #raise ValueError("Could not update process")
    bot.polling()
    logging.basicConfig(level=logging.INFO)
print("Bot is running. If any crash is detected, the bot will automatically reboot. Enjoy")
logging.info("Bot is running. If any crash is detected, the bot will automatically reboot. Enjoy")
# Keep the bot running continuously, even if it crashes
while True:
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error: {e}")
        print("Restarting script in 5 seconds...")
        logging.info("Restarting script in 5 seconds...")
        time.sleep(5)  # Wait for 5 seconds before restarting