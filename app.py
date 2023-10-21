import os

from flask import Flask, request, abort
from dotenv import load_dotenv

import requests
import json

from linebot.v3 import (WebhookHandler)
from linebot.models import (TemplateSendMessage)
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
from OpenAIHelper.chat import load_chat_template_safe

app = Flask(__name__)

load_dotenv()
channel_secret = os.getenv('CHANNEL_SECRET')
access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
openai.api_key = os.getenv("OPENAI_API_KEY")

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=access_token)


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

        if event.message.text == "> 重設場景":
            source_id = ""

            if event.source.type == "user":
                source_id = event.source.user_id
            elif event.source.type == "room":
                source_id = event.source.room_id
            else:
                source_id = event.source.group_id

            api_url = 'https://api.line.me/v2/bot/message/push'

            header = {'Content-Type': 'application/json', 'Authorization': f"Bearer ${access_token}"}
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
        # TODO: migrate to OpenAIHelper/
        elif event.message.text.startswith("> "):
            reply = '<failed to process the chat>'
            try:
                user_msg = event.message.text[2:]

                role_play_tmpl = load_chat_template_safe(
                        'role-play.system',
                        {
                            "story": """
I'm sitting in a college classroom where freshman training is ongoing. I am kind of unfamiliar with the school or even the city. I am curious about the news of club events, colleague activities, and school announcements, but I do not know if I can acquire that news.
You sit next to me, who is able and willing to offer me help. You can be anyone, such as a senior student, a teaching assistant, or even an experienced college staff in National  Yang Ming Chaio Tung University.
""",
                            "rules": """
- "Please engage in a daily conversation with me, while role-playing."
- "Avoid mentioning your nature as an AI language model unless I specifically refer to it in my prompts or in case of ethical violations. Thank you."
- "Always print the reply in the format: '[character name]: reply message...'"
""",
                            "postscript": """
The following links offers informations and recent announcements of the campus:
School website (time & news in english): https://en.nycu.edu.tw/
Admission Guide for New Students: https://newstudents.nycu.edu.tw/
Public facebook club of campus: https://www.facebook.com/NYCUSACTCampus/?locale=zh_TW
"""
                        }
                    )

                grammar_tmpl = load_chat_template_safe(
                        'grammar.user',
                        {
                            "content": user_msg
                        }
                    )

                chat_completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "system",
                        "content": role_play_tmpl
                    }, {
                        "role": "user",
                        "content": user_msg
                    }]
                )

                grammar_completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "system",
                        "content": "You are a friendly writing assistant."
                    }, {
                        "role": "user",
                        "content": grammar_tmpl
                    }]
                )

                app.logger.debug("Chat completed with response: %s", chat_completion)
                app.logger.debug("Grammar completed with response: %s", grammar_completion)
                reply = f"""{chat_completion.choices[0].message.content}
---
{grammar_completion.choices[0].message.content}
"""
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
