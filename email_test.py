import requests

#token : 6149367572:AAHK6f19zie10OXbEylyQbNXwA3E2xeWYsE
#chat_id : 713496494

#https://api.telegram.org/bot6149367572:AAHK6f19zie10OXbEylyQbNXwA3E2xeWYsE/getUpdates

def send_message(chat_id, text, token):
    url = f"https://api.telegram.org/bot6149367572:AAHK6f19zie10OXbEylyQbNXwA3E2xeWYsE/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, params=params)
    return response.json()


bot_token = '6149367572:AAHK6f19zie10OXbEylyQbNXwA3E2xeWYsE'
chat_id = '713496494'  # The chat ID of the user or group you want to send the message to
message_text = 'test2'

# Call the function to send the message
send_message(chat_id, message_text, bot_token)
