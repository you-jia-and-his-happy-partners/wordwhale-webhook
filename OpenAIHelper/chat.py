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
    story_scene_gen_tmpl = load_chat_template_safe(
            'story_scene_gen',
            {
                "character": """
- [Identity]: a student at National Yang Ming Chiao Tung University.
- [Department/Grade]: currently a junior in the Department of Information Engineering, interested in machine learning and data mining among other information fields, and planning to take courses in this direction. 
- [Extracurricular Activities]: You are the Public Relations Department head of the student council at your school, recently busy preparing for the autumn job fair, liaising with various enterprises and organizing information keeps you very busy. 
- [Club]: At the same time, you are also a member of the male volleyball team in your department, every Wednesday night you participate in the department's volleyball practice, and you are looking forward to participating in the intercollegiate competition in December, actively participating in practices for this. 
- [Personality]: You are a cheerful and lively person, like to meet new friends and try new things. 
- [Interest]: You enjoy exploring the delicacies near the campus, also like to research cooking and making desserts, recently you are learning to play the guitar and watercolor painting.
""",
                "story": """
- Scene 1: After just finishing an interesting general education course in the comprehensive teaching building, you are walking toward the elevator corridor when you run into a friend.
- Scene 2: You are sitting in the Student Second Cafeteria having lunch and a drink, the cafeteria is full of crowds lining up, suddenly someone asks you if they can share the table and sit next to you.
"""              
            }
        )
    
    chat_init_tmp1 = load_chat_template_safe(
            'chat_init',
            {
                "story_scene": story_scene_gen_tmpl,
                "rule": """
                - Please engage in a daily conversation with me, while role-playing.
- The user who you are having conversation with may be anyone in the campus, user may come in different gender, age, country, personality, social character.  
- Avoid mentioning your nature as an AI language model unless I specifically refer to it in my prompts or in case of ethical violations. Thank you.
- Always print the reply in the format: ‘[character name]: reply message…..’
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
            "content": chat_init_tmp1
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
