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
    AudioMessage,
)
from linebot.v3.webhooks import (MessageEvent, TextMessageContent, AudioMessageContent)
import openai

from CarouselTemplateFactory.CarouselTemplateFactory import (
    SceneCarouselTemplateFactory)
from OpenAIHelper.chat import (chat_default, chat_with_character_trait, chat_random, multi_chat_default)
from AWSTranslate.translate import (translate_en_zh)
from AzureSpeechToText.SpeechToText import (
    get_text_with_content,
    get_text_with_url,
)
from AzureTextToSpeech.TextToSpeech import (get_speech_file_link)

from flask_sqlalchemy import SQLAlchemy

from DBHelper import DBHelper

# create the extension
db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////app/data/chat.db"
db.init_app(app)


# Define the model with columns id (user id or group id), grammar_on, caption_on
class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    grammar_on = db.Column(db.Boolean, default=False)
    caption_on = db.Column(db.Boolean, default=False)
    translation_on = db.Column(db.Boolean, default=False)


class SceneState(db.Model):
    id = db.Column(db.String, primary_key=True)
    scene = db.Column(db.String)
    identity = db.Column(db.String)
    departmentGrade = db.Column(db.String)
    extracurricularActivities = db.Column(db.String)
    club = db.Column(db.String)
    personality = db.Column(db.String)
    interest = db.Column(db.String)


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

        if DBHelper.UserDBHelper.select_data(User, app, source_id) is False:
            DBHelper.UserDBHelper.insert_data(
                User, app, db, source_id, False, False, False)

        msg_to = _get_message_target(event)
        if event.message.text == "> 場景切換":
            if msg_to in _user_chat_cache:
                del _user_chat_cache[msg_to]
            
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
            data = DBHelper.UserDBHelper.select_data(User, app, source_id)
            DBHelper.UserDBHelper.update_flags(
                User, app, db,
                data["id"], not data["grammar_on"],
                data["caption_on"], data["translation_on"])
            
            reply_message(
                "文法糾正已切換為 {}".format(('開啟', '關閉')[data['grammar_on']])
            )
        elif event.message.text == "> 語音輔助字幕顯示":
            data = DBHelper.UserDBHelper.select_data(User, app, source_id)
            DBHelper.UserDBHelper.update_flags(
                User, app, db,
                data["id"], data["grammar_on"],
                not data["caption_on"], data["translation_on"])
            
            reply_message(
                "語音輔助字幕已切換為 {}".format(('開啟', '關閉')[data['caption_on']])
            )
        elif event.message.text == "> 中文輔助字幕顯示":
            data = DBHelper.UserDBHelper.select_data(User, app, source_id)
            DBHelper.UserDBHelper.update_flags(
                User, app, db,
                data["id"], data["grammar_on"],
                data["caption_on"], not data["translation_on"])
            
            reply_message(
                "中文輔助字幕已切換為 {}".format(('開啟', '關閉')[data['translation_on']])
            )
        elif event.message.text == "> 重設對話":
            if msg_to in _user_chat_cache:
                del _user_chat_cache[msg_to]
        elif event.message.text.startswith("> 場景設定:"):
            scene = event.message.text[7:]
            # SceneStateDBHelper
            if scene == "隨機":
                reply = reply_chat_random_scene_and_character(msg_to)
                reply_message(reply)
            else:
                DBHelper.SceneStateDBHelper.delete_data(SceneState, app, db, msg_to)
                DBHelper.SceneStateDBHelper.insert_data(
                    SceneState, app, db, msg_to, scene)
                reply_message("During this process, "
                              "you'll design the character you want to chat "
                              "with in 6 aspects\n"
                              "which are"
                              "Identity, Department/Grade, "
                              "Extracurricular Activities, Club, Personality, "
                              "Interest\n"
                              "[Notice] Please fill in following information "
                              "in English to build the "
                              "character you chat with:\n"
                              "- [Identity]: ")
        else:
            scene_state = DBHelper.SceneStateDBHelper.select_data(
                SceneState, app, msg_to)
            
            sections = ['reply']
            data = DBHelper.UserDBHelper.select_data(User, app, source_id)
            if data["grammar_on"]:
                sections.append('grammar')

            if scene_state is False:
                reply = reply_chat_cached(msg_to, event.message.text,
                                          sections=sections, line_bot_api=line_bot_api)
                reply_message(reply)
            else:
                characterSettings = [
                    "identity",
                    "departmentGrade",
                    "extracurricularActivities",
                    "club",
                    "personality",
                    "interest"
                ]

                replyMsgCharacterSettings = {
                    "identity": "- [Identity]: ",
                    "departmentGrade": "- [Department/Grade]: ",
                    "extracurricularActivities": "- [Extracurricular Activities]: ",
                    "club": "- [Club]: ",
                    "personality": "- [Personality]: ",
                    "interest": "- [Interest]: "
                }

                for i in range(len(characterSettings)):
                    setting = characterSettings[i]
                    if scene_state[setting] == "":
                        scene_state[setting] = replyMsgCharacterSettings[setting] + event.message.text
                        if i + 1 < len(characterSettings):
                            nextSetting = characterSettings[i+1]
                            reply_message(replyMsgCharacterSettings[nextSetting])
                            DBHelper.SceneStateDBHelper.update_data(
                                SceneState, app, db, msg_to, scene_state)
                        else:
                            # Create a chat hist with given parameter.
                            DBHelper.SceneStateDBHelper.delete_data(
                                SceneState, app, db, msg_to)

                            character_trait = ""
                            for setting in characterSettings:
                                character_trait = character_trait + "\n" + scene_state[setting]

                            reply = reply_chat_cached_with_character_trait(
                                msg_to,
                                character_trait,
                                scene_state["scene"],
                                sections)
                            
                            reply_message(reply)
                        break


@handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        audio_file_url = ""
        audio_file_content = ""
    
        if event.message.content_provider.type == "line":
            message_id = event.message.id
            contentUrl = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
            header = {'Authorization': f"Bearer {access_token}"}
            response = requests.get(contentUrl, headers=header)
            audio_file_content = response.content
        else:
            audio_file_url = event.message.original_content_url

        # get id
        source_id = ""

        if event.source.type == "user":
            source_id = event.source.user_id
        elif event.source.type == "room":
            source_id = event.source.room_id
        else:
            source_id = event.source.group_id

        # select data
        data = DBHelper.UserDBHelper.select_data(User, app, source_id)

        receive_text = ""

        # speech to text
        if audio_file_url != "":
            receive_text = get_text_with_url(audio_file_url)
        else:
            receive_text = get_text_with_content(audio_file_content)

        app.logger.debug("Receive text: %s", receive_text)

        # ChatGPT
        msg_to = _get_message_target(event)
        reply_text = reply_chat_cached(msg_to, receive_text, sections=['reply'])

        # text to speech
        reply_audio, audio_file_duration = get_speech_file_link(reply_text)

        # reply audio file
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[AudioMessage(originalContentUrl=reply_audio,
                                       duration=audio_file_duration)]
            )
        )

        # check if caption_on and reply
        if (data["caption_on"]):
            _reply_text_with_push_message_api(source_id, reply_text)

        # check if translation_on and reply
        if (data["translation_on"]):
            reply_zh = translate_en_zh(reply_text)
            _reply_text_with_push_message_api(source_id, reply_zh)


def _reply_text_with_push_message_api(source_id, text):
    api_url = 'https://api.line.me/v2/bot/message/push'

    header = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer ${access_token}"
    }

    body = {
        "to": source_id,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    req = requests.post(api_url, headers=header, data=json.dumps(body))
    app.logger.debug(req.text)


def reply_chat_cached(msg_to, user_msg, sections=['reply', 'grammar'], user_id=None, line_bot_api=None):
    reply = '<failed to process the chat>'
    try:
        if user_id and line_bot_api:
            # TODO: refactor the workaround
            username = line_bot_api.get_profile(user_id)
            user_msg = f'[{username}] {user_msg}'

        chat_id = None
        if msg_to in _user_chat_cache:
            chat_id = _user_chat_cache[msg_to]

        section_reply, _user_chat_cache[msg_to] = multi_chat_default(user_msg, chat_id=chat_id)
        # section_reply, _user_chat_cache[msg_to] = chat_default(user_msg, chat_id=chat_id)

        reply = "\n---\n".join(section_reply[sect] for sect in sections if sect in section_reply)
    except openai.error.RateLimitError:
        reply = '<quota exceeded, please report the issue>'

    return reply


def reply_chat_cached_with_character_trait(msg_to, character_trait, scene, sections=['reply', 'grammar']):
    reply = '<failed to process the chat>'
    try:
        section_reply, _user_chat_cache[msg_to] = chat_with_character_trait(character_trait, scene)
        reply = "\n---\n".join(section_reply[sect] for sect in sections)
    except openai.error.RateLimitError:
        reply = '<quota exceeded, please report the issue>'

    return reply


def reply_chat_random_scene_and_character(msg_to):
    reply = '<failed to process the chat>'
    try:
        section_reply, _user_chat_cache[msg_to] = chat_random()
        reply = f"{section_reply['reply']}\n---\nHere's the story settings:\nScene: {section_reply['scene']}\nCharacter: {section_reply['character']}"
    except openai.error.RateLimitError:
        reply = '<quota exceeded, please report the issue>'

    return reply


def _get_message_target(event):
    # globally enable multi-user chat
    if event.source.type == "user":
        return event.source.user_id
    elif event.source.type == "room":
        return event.source.room_id
    else:
        return event.source.group_id
