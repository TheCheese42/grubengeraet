from pathlib import Path
from threading import Thread
from typing import Iterable
import re

import requests

VERBOSE = True


def set_verbose(value: bool = True):
    global VERBOSE
    VERBOSE = value


def fetch_new_pages(
    base_url: str, working_dir: Path | str = Path.cwd(), threaded: bool = True
) -> None:
    """Fetches only pages that aren't present yet. Useful for quickly updating
    the underlying data. Updates the latest saved page as well.

    Args:
        base_url (str): The threads base url.
        working_dir (Path | str, optional): The directory where files are
        created. Defaults to Path.cwd().
    """
    working_dir = Path(working_dir)
    try:
        last_available_page_path = sorted(
            [i for i in working_dir.iterdir() if i.is_file()]
        )[-1]
    except IndexError:
        raise ValueError("Working dir is empty, use a different function for "
                         "downloading all pages together.")
    last_available_page = int(re.findall(
        r"\d+", last_available_page_path.name)[0]
    )
    last_page = get_last_page(base_url)

    fetch_and_save_pages_concurrently(
        base_url=base_url,
        pages=range(last_available_page, last_page + 1),
        working_dir=working_dir,
    )


def fetch_and_save_all_pages_concurrently(
    base_url: str, working_dir: Path | str = Path.cwd()
) -> None:
    """Fetches and saves all pages of a thread concurrently.

    Args:
        base_url (str): The threads base url.
        working_dir (Path | str, optional): The directory where the files
        are created. Defaults to Path.cwd().
    """
    last_page = get_last_page(base_url)

    fetch_and_save_pages_concurrently(
        base_url=base_url,
        pages=range(1, last_page + 1),
        working_dir=working_dir,
    )


def fetch_and_save_pages_concurrently(
    base_url: str, pages: Iterable, working_dir: Path | str = Path.cwd()
) -> None:
    """Fetches and saves specified pages of a thread concurrently.

    Args:
        base_url (str): The threads base url.
        pages (Iterable): An iterable of pages to be fetched and saved.
        working_dir (Path | str, optional): The directory where the files
        are created. Defaults to Path.cwd().
    """
    threads = []
    for page in pages:
        thread = Thread(
            target=fetch_and_save,
            name=f"UW-Stats fetch thread #{page}",
            args=(get_url_for_page(base_url, page), Path(working_dir), page),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def fetch_and_save_all_pages_linearly(
    base_url: str, working_dir: Path | str = Path.cwd()
) -> None:
    """Fetches and saves all pages of a thread linearly.

    Args:
        base_url (str): The threads base url.
        working_dir (Path | str, optional): The directory where the files
        are created. Defaults to Path.cwd().
    """
    last_page = get_last_page(base_url)

    fetch_and_save_pages_linearly(
        base_url=base_url,
        pages=range(1, last_page + 1),
        working_dir=working_dir,
    )


def fetch_and_save_pages_linearly(
    base_url: str, pages: Iterable, working_dir: Path | str = Path.cwd()
) -> None:
    """Fetches and saves certain pages of a thread linearly.

    Args:
        base_url (str): The threads base url.
        pages (Iterable): An iterable of pages to be fetched and saved.
        working_dir (Path | str, optional): The directory where the files
        are created. Defaults to Path.cwd().
    """
    for page in pages:
        fetch_and_save(
            get_url_for_page(base_url, page), Path(working_dir), page
        )


def fetch_and_save(url: str, working_dir: Path, page_num: int) -> None:
    """Fetches the page behind the given url and saves it to a file.

    Args:
        url (str): The page url.
        working_dir (Path): The directory where the files are created.
        page_num (int): The page number.
    """
    html = fetch_page(url)
    save_page(html, working_dir, page_num)
    if VERBOSE:
        print(f"Saved page {page_num}.")


def get_last_page(base_url: str, max: int = 1_000_000) -> int:
    """Finds the last page of a given thread. Does it by requesting
    an unlikely large page number and watching the redirect.

    Args:
        base_url (str): The base url to the thread.
        max (int, optional): The max value of pages the thread is expected to
        have. Defaults to 1_000_000.

    Returns:
        int: The max page's number.
    """
    url = get_url_for_page(base_url, max)
    last_page_url = requests.get(url).url
    return get_page_from_url(last_page_url)


def get_page_from_url(url: str, max: int = 1_000_000) -> int:
    """Extracts the page number from a thread url.

    Args:
        url (str): The thread url.

    Returns:
        int: The page number.
    """
    # Get the number at the end of the url
    # Too lazy for regexp :|
    if url[-1] == "/":  # No page indicator (first page)
        return 1

    num = ""
    for i in range(1, max):
        if not (n := url[-i]).isdigit():
            break
        num += n
    return int(num[::-1])


def get_url_for_page(base_url: str, page_num: int) -> str:
    """Generates an url pointing to a page using the base thread url
    and the page number.

    Args:
        base_url (str): The threads base url. Must have a trailing slash.
        page_num (int): The page number.

    Returns:
        str: The full url linking to the page in the thread.
    """
    return base_url + f"page-{page_num}/"


def fetch_page(url: str) -> str:
    """Fetches a webpage and returns the raw HTML content using requests.get().

    Args:
        url (str): The URL to the webpage.

    Returns:
        str: The raw HTML content.
    """
    response = requests.get(url)
    return response.text


def save_page(html: str, working_dir: Path, page_num: int = 1) -> int:
    """Saves a given page to an HTML file.

    Args:
        html (str): The raw HTML content.
        working_dir (Path): The directory where the file will be saved.
        page_num (int, optional): The page number. Defaults to 1.

    Returns:
        int: The amount of bytes written.
    """
    assert working_dir.is_dir(), "path arg must be a directory."
    file_path = working_dir / f"page_{str(page_num).zfill(4)}.html"
    with open(file_path, mode="w", encoding="utf-8") as fp:
        return fp.write(html)
