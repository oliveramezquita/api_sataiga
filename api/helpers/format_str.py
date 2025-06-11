import re


def clean_text(text):
    clean = re.sub(r'[^a-zA-Z]', '', text)
    return clean
