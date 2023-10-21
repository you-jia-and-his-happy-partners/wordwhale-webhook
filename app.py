import os

from flask import Flask, request, abort
from dotenv import load_dotenv

import requests
import json

from linebot.v3 import (WebhookHandler)
from linebot.v3.exceptions import (InvalidSignatureError)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (MessageEvent, TextMessageContent)
import openai

from CarouselTemplateFactory.CarouselTemplateFactory import (
    SceneCarouselTemplateFactory)
from OpenAIHelper.chat import (chat_default)

from flask_sqlalchemy import SQLAlchemy


# create the extension
db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////app/data/chat.db"
db.init_app(app)

load_dotenv()
channel_secret = os.getenv('CHANNEL_SECRET')
access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
openai.api_key = os.getenv("OPENAI_API_KEY")

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=access_token)

_user_chat_cache = {}


def create_table():
    with app.app_context():
        db.create_all()
        app.logger.debug("DB table created!")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. " +
              "Please check your channel access token/channel secret.")
        abort(400)

    return channel_secret


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        msg_to = str(event.source)
        if event.message.text == "> 重設場景":
            source_id = ""

            if event.source.type == "user":
                source_id = event.source.user_id
            elif event.source.type == "room":
                source_id = event.source.room_id
            else:
                source_id = event.source.group_id

            api_url = 'https://api.line.me/v2/bot/message/push'

            header = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer ${access_token}"
            }
            
            body = {
                "to": source_id,
                "messages": [
                    {
                        "type": "template",
                        "altText": "scene selction carousel",
                        "template": SceneCarouselTemplateFactory()
                    }
                ]
            }

            req = requests.post(api_url, headers=header, data=json.dumps(body))

            app.logger.debug(req.text)
        # DEBUG: reply to '> [...]' msg with chatGPT
        elif event.message.text == "> 重設對話":
            if msg_to in _user_chat_cache:
                del _user_chat_cache[msg_to]
        elif event.message.text.startswith("> "):
            reply = '<failed to process the chat>'
            try:
                user_msg = event.message.text[2:]
                chat_id = None
                if msg_to in _user_chat_cache:
                    chat_id = _user_chat_cache[msg_to]

                reply, _user_chat_cache[msg_to] = chat_default(user_msg, chat_id=chat_id)
            except openai.error.RateLimitError:
                reply = '<quota exceeded, please report the issue>'

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(reply_token=event.reply_token,
                                    messages=[TextMessage(text=reply)]))
        else:
            # echo msg
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=event.message.text)]))
