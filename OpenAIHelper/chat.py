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
    character_gen_tmpl = load_chat_template_safe(
            'character_gen',
            {
                "user_input": """
- [Identity]: a exchange senior student from France
- [Department/Grade]: major in management science 
- [Extracurricular Activities/Club]: attend dessert club
- [Personality]: shy, heartwarming, willing to try new things and meet new friends
- [Interest]: still learning to play piano, love to watch popular anime
                """
            }
        )
    
    story_scene_gen_tmpl = load_chat_template_safe(
            'story_scene_gen',
            {
                "character": character_gen_tmpl,
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
                "rules": """
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
    sections = {
        "reply": chat_completion.choices[0].message.content,
        "grammar": grammar_completion.choices[0].message.content
    }
    return sections, chat_completion.id


def chat_with_character_trait(character_trait, target_scene):
    scenes = [
        "- Scene: After just finishing an interesting general education course in the comprehensive teaching building, you are walking toward the elevator corridor when you run into a friend.",
        "- Scene: You are sitting in the Student Second Cafeteria having lunch and a drink, the cafeteria is full of crowds lining up, suddenly someone asks you if they can share the table and sit next to you."
    ]

    scene = ""
    if target_scene == "電梯":
        scene = scenes[0]
    else:
        scene = scenes[1]

    character_gen_tmpl = load_chat_template_safe(
            'character_gen',
            {
                "user_input": character_trait
            }
        )
    
    chat_hist = [{
        "role": "system",
        "content": character_gen_tmpl
    }]

    character_gen_chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    character_gen = character_gen_chat_completion.choices[0].message

    story_scene_gen_tmpl = load_chat_template_safe(
            'story_scene_gen',
            {
                "character": character_gen,
                "story": scene,
            }
        )
    
    chat_hist = [{
        "role": "system",
        "content": story_scene_gen_tmpl
    }]

    story_scene_gen_chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    story_scene_gen = story_scene_gen_chat_completion.choices[0].message

    
    chat_init_tmpl = load_chat_template_safe(
            'chat_init',
            {
                "story_scene": story_scene_gen,
                "rules": """
                - Please engage in a daily conversation with me, while role-playing.
- The user who you are having conversation with may be anyone in the campus, user may come in different gender, age, country, personality, social character.  
- Avoid mentioning your nature as an AI language model unless I specifically refer to it in my prompts or in case of ethical violations. Thank you.
- Always print the reply in the format: ‘[character name]: reply message…..’
"""
            }
    )

    chat_hist = [{
        "role": "system",
        "content": chat_init_tmpl
    }]

    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    chat_id = chat_completion.id
    chat_hist.append(chat_completion.choices[0].message)
    _chat_cache[chat_id] = chat_hist

    logger.debug("Chat completed with response: %s", chat_completion)
    sections = {
        "reply": chat_completion.choices[0].message.content,
        "grammar": ""
    }
    return sections, chat_completion.id

# Set character and scene randomly
def chat_random():
    # STEP1: generate character randomly
    # get template
    character_gen_tmpl = load_chat_template_safe("random_character_gen", {})

    # send to openai and get result
    chat_hist = [{
            "role": "user",
            "content": character_gen_tmpl
        }]

    chat_completion_1 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    short_character_description = chat_completion_1.choices[0].message.content

    # STEP2: refine character setting
    character_refine_tmpl = load_chat_template_safe(
            'random_character_refine',
            {
                "step1_result": short_character_description
            }
        )

    chat_hist = [{
            "role": "user",
            "content": character_refine_tmpl
        }]
    chat_completion_2 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    character_description = chat_completion_2.choices[0].message.content

    # STEP3: generate scene
    scene_gen_tmpl = load_chat_template_safe(
            'random_scene_gen',
            {
                "step2_result": character_description
            }
        )

    chat_hist = [{
            "role": "user",
            "content": scene_gen_tmpl
        }]
    
    chat_completion_3 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    scene_description = chat_completion_3.choices[0].message.content

    # STEP4: create starting dialog based on STEP2 and STEP3
    dialog_start_tmpl = load_chat_template_safe(
            'random_dialog_start',
            {
                "step2_result": character_description,
                "step3_result": scene_description
            }
        )

    chat_hist = [{
            "role": "user",
            "content": dialog_start_tmpl
        }]
    
    chat_completion_4 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_hist
    )

    _chat_id = chat_completion_4.id
    chat_hist.append(chat_completion_4.choices[0].message)
    _chat_cache[_chat_id] = chat_hist

    # Return values
    sections = {
        "reply": chat_completion_4.choices[0].message.content,
        "scene": scene_description,
        "character": character_description,
        "grammar": ""
    }

    return sections, _chat_id


def multi_chat_character_gen_default(user_msg, chat_id=None):
    """
    Default multi-user chat function. Passes `user_msg` with templates to ChatGPT.
    """
    multi_character_gen_tmpl = load_chat_template_safe(
            'character_gen',
            {
                "user_input": """
- [Identity]: a exchange senior student from France
- [Department/Grade]: major in management science 
- [Extracurricular Activities/Club]: attend dessert club
- [Personality]: shy, heartwarming, willing to try new things and meet new friends
- [Interest]: still learning to play piano, love to watch popular anime
                """
            }
        )
    return multi_character_gen_tmpl


def multi_chat_summarization_default(user_msg, chat_id=None):
    """
    Default multi-user chat summarization function. Passes `user_msg` with templates to ChatGPT.
    """

    if chat_id and chat_id not in _chat_cache:
        logger.warning("Ignoring invalid chat id '%s'", chat_id)
        chat_id = None

    if not chat_id:
        chat_hist = [{
            "role": "system",
            "content": multi_chat_character_gen_default(user_msg, chat_id=chat_id)
        }]
    else:
        assert chat_id in _chat_cache
        chat_hist = _chat_cache[chat_id]

    chat_hist.append({
        "role": "user",
        "content": user_msg
    })

    multi_chat_summarization_tmpl = load_chat_template_safe( #Q
            'summary',
            {
                "history": chat_hist
            }
    )

    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": multi_chat_summarization_tmpl
        }]
    )

    chat_id = chat_completion.id
    chat_hist.append(chat_completion.choices[0].message)
    _chat_cache[chat_id] = chat_hist

    logger.debug("Chat completed with response: %s", chat_completion)
    # sections = {
    #     "reply": chat_completion.choices[0].message.content,
    # }
    return chat_hist


def multi_chat_default(user_msg, chat_id=None):
    """
    Default multi-user chat function. Passes `user_msg` with templates to ChatGPT.
    """
    multi_chat_tmpl = load_chat_template_safe(
            'multi_chat_reply',
            {
                "user_input": multi_chat_summarization_default(user_msg, chat_id=chat_id)
            }
    )
    chat_completion = openai.Completion.create(
        model="gpt-3.5-turbo",
        messages=multi_chat_tmpl
    )
    chat_id = chat_completion.id
    chat_hist.append(chat_completion.choices[0].message)
    _chat_cache[chat_id] = chat_hist

    logger.debug("Chat completed with response: %s", chat_completion)
    sections = {
        "reply": chat_completion.choices[0].message.content,
    }
    return sections, chat_completion.id
