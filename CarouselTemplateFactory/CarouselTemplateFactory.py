import os
from dotenv import load_dotenv
from linebot.models import (CarouselTemplate, CarouselColumn, MessageAction)


def SceneCarouselTemplateFactory():
    load_dotenv()
    sas_token = os.getenv('SAS_TOKEN')

    _thumbnail_image_urls = [
        'https://wordwhalestorage.file.core.windows.net/hackathon'
        '/resturant.jpeg' + sas_token,
        'https://wordwhalestorage.file.core.windows.net/hackathon'
        '/question_mark.png' + sas_token,
    ]

    _titles = ['電梯前', '學生餐廳', '隨機']
    _texts = ['上完通識課等電梯時，遇到...', '在餐廳吃飯時，遇到...', '隨機配對聊天對象和情境']
    _actions = [{
        'label': '> 場景設定:電梯前',
        'text': '> 場景設定:電梯前'
    }, {
        'label': '> 場景設定:學生餐廳',
        'text': '> 場景設定:學生餐廳'
    }, {
        'label': '> 場景設定:隨機',
        'text': '> 場景設定:隨機'
    }]

    return {
        "type": "carousel",
        "columns": _CarouselColumnTemplate(
            _thumbnail_image_urls, _titles, _texts, _actions)
    }


def _CarouselColumnTemplate(thumbnail_image_urls, titles, texts, actions):
    columns = []
    for i in range(len(titles)):
        columns.append(
            {
                "thumbnailImageUrl": thumbnail_image_urls[i],
                "title": titles[i],
                "text": texts[i],
                "actions": [
                    {
                        "type": "message",
                        "label": actions[i]['label'],
                        "text": actions[i]['text']
                    }
                ]
            }
        )
    return columns
