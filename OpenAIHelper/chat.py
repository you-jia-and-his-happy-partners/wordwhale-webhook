from string import Template

# import openai


def load_chat_template_safe(name, mapping):
    """
    Load chat template with `name` (resource/chat-template/${name}.chat),
    and *safe* substitute mapping with string.Template.
    """
    with open(f"resource/chat-template/{name}.chat", encoding='utf-8') as chatfile:
        content = chatfile.read()

    tmpl = Template(content)
    return tmpl.safe_substitute(mapping)
