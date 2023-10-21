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

from DBHelper import DBHelper

# create the extension
db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////app/data/chat.db"
db.init_app(app)


# Define the model with columns id (user id or group id), session_id, grammar_on, caption_on
class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    session_id = db.Column(db.String)
    grammar_on = db.Column(db.Boolean, default=False)
    caption_on = db.Column(db.Boolean, default=False)
    translation_on = db.Column(db.Boolean, default=False)

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

        def reply_message(text):
            # echo msg
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=text)]))

        source_id = ""

        if event.source.type == "user":
            source_id = event.source.user_id
        elif event.source.type == "room":
            source_id = event.source.room_id
        else:
            source_id = event.source.group_id

        msg_to = str(event.source)
        if event.message.text == "> 場景切換":
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
        elif event.message.text == "> 文法糾正":
            data = DBHelper.select_data(User, app, source_id)
            DBHelper.update_flags(
                User, app, db,
                data["id"], not data["grammar_on"],
                data["caption_on"], data["translation_on"])
            
            reply_message(
                "文法糾正已切換為 {}".format(('開啟', '關閉')[data['grammar_on']])
            )
        elif event.message.text == "> 語音輔助字幕顯示":
            data = DBHelper.select_data(User, app, source_id)
            DBHelper.update_flags(
                User, app, db,
                data["id"], data["grammar_on"],
                not data["caption_on"], data["translation_on"])
            
            reply_message(
                "語音輔助字幕已切換為 {}".format(('開啟', '關閉')[data['caption_on']])
            )
        elif event.message.text == "> 中文輔助字幕顯示":
            data = DBHelper.select_data(User, app, source_id)
            DBHelper.update_flags(
                User, app, db,
                data["id"], data["grammar_on"],
                data["caption_on"], not data["translation_on"])
            
            reply_message(
                "中文輔助字幕已切換為 {}".format(('開啟', '關閉')[data['translation_on']])
            )
        elif event.message.text == "> 重設對話":
            if msg_to in _user_chat_cache:
                del _user_chat_cache[msg_to]
        # DEBUG: reply to '> [...]' msg with chatGPT
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

            reply_message(reply)
        else:
            reply_message(event.message.text)
