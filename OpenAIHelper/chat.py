import logging
from string import Template

import openai


logger = logging.getLogger(__name__)
_chat_cache = {}


def load_chat_template_safe(name, mapping):
    """
    Load chat template with `name` (resource/chat-template/${name}.chat),
    and *safe* substitute mapping with string.Template.
    """
    with open(f"resource/chat-template/{name}.chat", encoding='utf-8') as chatfile:
        content = chatfile.read()

    tmpl = Template(content)
    return tmpl.safe_substitute(mapping)


def chat_default(user_msg, chat_id=None):
    """
    Default chat function. Passes `user_msg` with templates to ChatGPT.
    """
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

    if chat_id and chat_id not in _chat_cache:
        logger.warning("Ignoring invalid chat id '%s'", chat_id)
        chat_id = None

    grammar_tmpl = load_chat_template_safe(
            'grammar.user',
            {
                "content": user_msg
            }
        )

    if not chat_id:
        chat_hist = [{
            "role": "system",
            "content": role_play_tmpl
        }]
    else:
        assert chat_id in _chat_cache
        chat_hist = _chat_cache[chat_id]

    chat_hist.append({
        "role": "user",
        "content": user_msg
    })
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    chat_id = chat_completion.id
    chat_hist.append(chat_completion.choices[0].message)
    _chat_cache[chat_id] = chat_hist

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

    logger.debug("Chat completed with response: %s", chat_completion)
    logger.debug("Grammar completed with response: %s", grammar_completion)
    reply = f"""{chat_completion.choices[0].message.content}
---
{grammar_completion.choices[0].message.content}
"""
    return reply, chat_completion.id
