import emoji

EMOJI_LIST = list(emoji.EMOJI_DATA.keys())


def is_emoji(string: str) -> bool:
    try:
        return string in EMOJI_LIST
    except IndexError:  # Empty string
        return False
