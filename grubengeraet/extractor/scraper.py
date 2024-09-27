# Parts of this code are inspired by or copied from
# https://github.com/ifscript/lootscript.
# This notice is also found at the top of affected functions.

import copy
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional

import bs4
import dateparser
import pandas as pd
import regex as re  # See rules_reworked()

from .emojis import is_emoji

WHITESPACES = "".join([
  chr(i) for i in [847, 4447, 4448, 6068, 6069, 32]
])

# Source: https://de.m.wikipedia.org/wiki/Satzzeichen
PUNCTUATION = r".?!\"„“‚‘»«‹›,;:'’–—‐\-·/\()\[\]<>{}…☞‽¡¿⸘、"

COLUMNS = [
    "post_id",
    "post_num",
    "page_num",
    "author",
    "author_id",
    "creation_datetime",
    "content",
    "like_count",
    "quote_count",
    "quoted_list",
    "spoiler_count",
    "mentions_count",
    "mentioned_list",
    "word_count",
    "words",
    "emoji_count",
    "emoji_frequency_mapping",
    "is_edited",
    "is_rules_compliant",
    "rulebreak_reasons",
]

# bs4 seems to recursively parse the html. Errors sometimes.
sys.setrecursionlimit(10_000)


def get_page_for_message(post_num: int) -> int:
    """Finds the page a given post should be in.

    Args:
        post_num (int): The post number.

    Returns:
        int: The page number.
    """
    return math.ceil(post_num / 20)


def get_first_post_from_page(page_num: int) -> int:
    """Returns the first post number on a given page.

    Args:
        page_num (int): The page number.

    Returns:
        int: The first post number.
    """
    return page_num * 20 - 19


def get_last_post_from_page(page_num: int) -> int:
    """Returns the last post number on a given page.

    Args:
        page_num (int): The page number.

    Returns:
        int: The last post number.
    """
    return page_num * 20


def find_all_messages(soup: bs4.BeautifulSoup) -> list[bs4.element.Tag]:
    """Returns a list of message article tags.

    Args:
        soup (bs4.BeautifulSoup): The BeautifulSoup object of the HTML page.

    Returns:
        list[bs4.element.Tag]: The list containing the message article tags.
    """
    return soup.find_all("article", class_="message")  # type: ignore[no-any-return]  # noqa


def find_message_content(message: bs4.element.Tag) -> bs4.element.Tag:
    """Retrieves the content from a message.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        bs4.element.Tag: The message content's element tag object.
    """
    return message.find("div", class_="message-content")


def construct_dataframe(
    path: str | Path,
    pagerange: Optional[range] = None,
    postrange: Optional[range] = None,
    silent: bool = False,
) -> pd.DataFrame:
    """Constructs a dataframe pagewise from HTML files.
    This could eventually be split up into multiple functions or a class.
    Use the *range parameters to specify what pages to be included in the
    output. Second range argument is exclusive.

    Args:
        path (str | Path): The path containing the HTML files.
        pagerange (range, optional): The pagerange to include in the table.
        Mutually exclusive with other ranges. Defaults to None.
        postrange (range, optional): The postrange to include in the table.
        Mutually exclusive with other ranges. Defaults to None.

    Returns:
        pd.DataFrame: The newly created dataframe.
    """
    if all([pagerange, postrange]):
        raise ValueError("Only one *range parameter can be given.")

    series_list = []
    for file in sorted(
        Path(path).iterdir(), key=lambda s: re.findall(r"\d+", s.name)[0]
    ):
        if file.is_dir():
            continue
        page_num = int(re.findall(r"\d+", file.name)[0])

        # range checks
        if pagerange:
            if page_num not in pagerange:
                continue
        if postrange:
            if (
                get_first_post_from_page(page_num) not in postrange and
                get_last_post_from_page(page_num) not in postrange
            ):
                continue

        if not silent:
            print("Processing", file)

        soup = bs4.BeautifulSoup(
            file.read_text("utf-8"), features="html.parser"
        )

        for message in find_all_messages(soup):
            post_id = get_post_id(message)
            post_num = get_post_num(message)
            if postrange:
                if post_num not in postrange:
                    continue
            # Some data-gathering functions need access to otherwise
            # noisy tags.
            # Every function tries to access the unmodified message by
            # default, unless it needs to work with content text or raw
            # HTML. Or needs to modify the message.
            unmodified_message = copy.copy(message)
            content_tag = find_message_content(message)  # Can be modified

            author = unmodified_message["data-author"]
            author_id = get_author_id(unmodified_message)
            creation_datetime = get_message_creation_time(
                unmodified_message
            ).isoformat()
            is_edited = has_edited_message(unmodified_message)

            quote_count = get_amount_of_quotes(unmodified_message)
            quoted_list = get_list_of_quoted_usernames(unmodified_message)

            spoiler_count = get_amount_of_spoilers(unmodified_message)

            mentioned_list = get_list_of_mentioned_ids(
                unmodified_message
            )
            mentions_count = len(mentioned_list)

            like_count = get_amount_of_likes(message)  # modifies

            clean_noisy_tags(message)  # modifies

            # Must come before clean_emojis()
            emoji_frequency_mapping = (
                get_mapping_of_emojis_and_frequency(message)  # Needs cleaned
            )
            emoji_count = sum(i for i in emoji_frequency_mapping.values())

            clean_emojis(message)  # modifies

            # Can't use built in strip=True argument here as that would strip
            # spaces around HTML tags within the content, resulting in a loss
            # of important spaces leading to rule violations.
            content = content_tag.get_text().strip()  # needs modified

            words = split_words(content)
            word_count = len(words)

            rules_compliance_check_result = rules_reworked(content, word_count)
            rulebreak_reasons = [
                k for k, v in rules_compliance_check_result.items() if not v
            ]
            is_rules_compliant = not rulebreak_reasons

            message_series = pd.Series(
                data=(
                    [
                        post_id,
                        post_num,
                        page_num,
                        author,
                        author_id,
                        creation_datetime,
                        content,
                        like_count,
                        quote_count,
                        quoted_list,
                        spoiler_count,
                        mentions_count,
                        mentioned_list,
                        word_count,
                        words,
                        emoji_count,
                        emoji_frequency_mapping,
                        is_edited,
                        is_rules_compliant,
                        rulebreak_reasons,
                    ]
                ),
                index=COLUMNS,
            )
            series_list.append(message_series)

    # XXX Seems important but causes error when the last page is shorter
    # if pagerange:
    #     index = range(
    #         get_first_post_from_page(pagerange[0]),
    #         get_last_post_from_page(pagerange[-1]) + 1,
    #     )
    # elif postrange:
    #     index = postrange
    # else:
    #     index = None

    df = pd.DataFrame(
        series_list,
        index=None,
        columns=COLUMNS,
        copy=False,
    )
    return df


def get_post_num(message: bs4.element.Tag) -> int:
    """Get the post number of a message.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        int: The post number.
    """
    postnum_str = message.find_all("li")[3].get_text(strip=True)[1:]
    return int(postnum_str.replace(".", ""))


def get_post_id(message: bs4.element.Tag) -> str:
    """
    Get the post id of a message.

    :param message: The message's element tag object.
    :type message: bs4.element.Tag
    :return: The post id.
    :rtype: str
    """
    match = re.search(r"post-(\d+)", message["data-content"])  # type: re.Match
    if not match:
        raise ValueError("Post does not have an ID.")
    return match.group(1)  # type: ignore[no-any-return]


def get_author_id(message: bs4.element.Tag) -> str:
    """
    Get the author id as string.

    :param message: The message's element tag object.
    :type message: bs4.element.Tag
    :return: The author's id
    :rtype: str
    """
    try:
        # Pings look the same, however the author comes first
        return message.find("a", class_="username")["data-user-id"]  # type: ignore[no-any-return]  # noqa
    except TypeError:
        # Deleted Member has no ID
        return "0"
    except KeyError:
        # First, a non-existent user that doesn't have the anchor tag at all
        # Second, that user pinged someone, that ping anchor is corrupt.
        # Corrupted Tag that doesn't have the data-user-id param. Ex.: https://uwmc.de/p102857  # noqa
        return "0"


def get_amount_of_likes(message: bs4.element.Tag) -> int:
    """Get the amount of likes a message has.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        int: The like count.
    """
    # Inspired by
    # https://github.com/ifscript/lootscript/blob/main/lootscript.py
    likes_bar = message.find("a", class_="reactionsBar-link")

    if likes_bar is None:
        # No likes found
        return 0

    num_likes = len(likes_bar.find_all('bdi'))

    if num_likes < 3:
        # Can be more if num_likes is 3
        return num_likes

    for bdi in likes_bar("bdi"):
        # Remove usernames
        bdi.decompose()

    text = likes_bar.get_text(strip=True)
    try:
        # Return additional likes plus the ones being counted
        return int(re.findall(r"\d+", text)[0]) + num_likes
    except IndexError:
        # There are just 3 likes
        return num_likes


def clean_noisy_tags(message: bs4.element.Tag) -> None:
    """Decomposes various hard-coded noisy Tags.

    Args:
        message (bs4.element.Tag): The message's element tag object.
    """
    # Media Tags have a noisy "Ansehen auf" string.
    for p in message.find_all("p"):
        if p.get_text(strip=True) == "Ansehen auf":
            p.decompose()

    # Tags whose content shouldn't be in the message content.
    # List of tuples. First tuple element is the tag string, second
    # an optional class.
    useless_tags: list[tuple[str, Optional[str]]] = [
        ("script", None),
        ("table", None),
        ("blockquote", None),
        ("div", "message-lastEdit"),
        ("button", None),
    ]
    for tag, class_ in useless_tags:
        if class_:
            all_tags = message.find_all(tag, class_=class_)
        else:
            all_tags = message.find_all(tag)
        for find in all_tags:
            find.decompose()


def clean_emojis(message: bs4.element.Tag) -> None:
    """Replaces emojis with dots.

    Args:
        message (bs4.element.Tag): The message's element tag object.
    """
    # ## Use data-shortname instead of alt, as unicode emojis will have their
    # ## actual symbol in alt, while having the description in data-shortname.
    # Turn emojis into their alt
    for emoji in message.find_all("img", class_="smilie"):
        try:
            emoji.insert_after(".")  # Use emojis as Sentence delimiter
            # XXX Would make emojis count as an additional word, possibly
            # XXX breaking the rules if at the beginning of the post (?)
            # XXX alt = emoji["data-shortname"]
            # XXX emoji.insert_before(alt)
            emoji.decompose()
        except (TypeError, ValueError):
            # Rare error of a corrupted image tag (?)
            # Just ignoring, it's all @fscript's fault.
            pass


def get_amount_of_quotes(message: bs4.element.Tag) -> int:
    """Retrieves the amount of quotes of a message.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        int: The quote count.
    """
    return len(message.find_all("blockquote", class_="bbCodeBlock--quote"))


def get_list_of_quoted_usernames(message: bs4.element.Tag) -> list[str]:
    """Retrieves a list of usernames being quoted in a message.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        list[str]: The list containing the usernames.
    """
    usernames: list[str] = []
    for quote in message.find_all("blockquote", class_="bbCodeBlock--quote"):
        usernames.append(quote["data-quote"])
    return usernames


def get_amount_of_spoilers(message: bs4.element.Tag) -> int:
    """Retrieves the amount of spoilers in a message.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        int: The spoiler count.
    """
    return len(message.find_all("div", class_="bbCodeSpoiler"))


def get_list_of_mentioned_ids(message: bs4.element.Tag) -> list[str]:
    """Retrieves a list of mentioned usernames. Get the amount of mentions
    by using len() on the list.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        list[str]: The list containing all usernames.
    """
    ids: list[str] = []
    for mention in message.find_all("a", class_="username")[1:]:
        # Ignore the first one, it's the post author
        try:
            ids.append(mention["data-user-id"])
        except KeyError:
            # Corrupt Mention Tag (ex.: https://uwmc.de/p90996)
            ids.append("0")
    return ids


def get_mapping_of_emojis_and_frequency(
    message: bs4.element.Tag
) -> dict[str, int]:
    """Returns a mapping from all occurring emojis to their frequency.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        dict[str, int]: A mapping from all occurring emojis to their frequency.
    """
    emojis: dict[str, int] = {}
    for emoji in message.find_all("img", class_="smilie"):
        alt = emoji["data-shortname"]
        if not emojis.get(alt):
            emojis[alt] = 1
            continue
        emojis[alt] += 1
    return emojis


def split_words(string_: str) -> list[str]:
    """Counts the amount of words in a string by utilizing the
    re.split() method. Splits on any whitespace character and
    discards empty strings.

    Args:
        string (str): The string to count the words from.

    Returns:
        int: The amount of words in the string.
    """
    # Should split this into 2: `two-worded` or into 3: `not.one"word`
    split = re.split(rf"[\s{PUNCTUATION}]", string_)
    return [i for i in split if re.search(r"\w", i)]


def has_edited_message(message: bs4.element.Tag) -> bool:
    """Check if the message has been edited at least once.

    Args:
        message (bs4.element.Tag): The message's element tag object.

    Returns:
        bool: Wether or not the message has been edited.
    """
    if message.find("div", class_="message-lastEdit"):
        return True
    return False


def get_message_creation_time(message: bs4.element.Tag) -> dt.datetime:
    """Retrieves a messages creation date.

    Args:
        message (bs4.element.Tag): The message's element tag.

    Returns:
        datetime.datetime: A datetime.datetime object representing the
        message's creation date.
    """
    iso_string = message.find_all("time", class_="u-dt")[0]["datetime"]
    return dateparser.parse(iso_string)  # type: ignore


def rules_reworked(content: str, word_count: int) -> dict[str, bool]:
    """
    Checks if a post is compliant to the rules defined for WALA.

    Rules:
        - At least 5 words (word_count)
        - First letter must be capitalized (first_letter)
        - Trailing punctuation (punctuation)

    :param content: The message content
    :type content: str
    :param word_count: Amount of words in the content
    :type word_count: int
    :return: Dictionary mapping criterion to wether it complies. Criteria are:
    word_count, first_letter, punctuation
    :rtype: dict[str, bool]
    """
    content = content.strip()  # Remove trailing and leading whitespaces
    content = content.strip(WHITESPACES)  # Better list

    compliance = {
        "word_count": True,
        "first_letter": True,
        "punctuation": True,
    }

    if not content:  # Empty message
        return {
            k: False for k in compliance.keys()
        }

    # Word count
    if word_count < 5:
        compliance["word_count"] = False

    # First Letter
    # Get index of first letter
    # This requires the third party regex module to work
    # Therefore `import regex as re`
    # This works with all Unicode letters, including äöü, ß and âáà.
    first_letter_match = re.search('\\p{L}', content, re.UNICODE)
    if (
        first_letter_match is None or  # No letter in content
        not first_letter_match.captures()[0].isupper()  # letter not uppercase
    ):
        compliance["first_letter"] = False

    # Punctuation
    # Last forum emoji has already been replaced with a dot
    last_char = content[-1]
    if (
        last_char not in PUNCTUATION and
        not is_emoji(last_char)
    ):
        compliance["punctuation"] = False

    return compliance
