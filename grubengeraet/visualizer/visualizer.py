import math
from contextlib import contextmanager
from datetime import datetime
from itertools import chain
from operator import itemgetter
from typing import Literal, Optional

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def mean(values: list[int | float]) -> float:
    return sum(values) / float(len(values))


class DataExtractor:
    """A class to extract various valuable data from a dataframe.
    """
    def __init__(
        self,
        df: pd.DataFrame,
        pagerange: Optional[range] = None,
        postrange: Optional[range] = None,
    ) -> None:
        """Initialize the Extractor by providing a dataframe and
        post/pageranges to specify the data to be analyzed. Ranges
        apply for every further method. Second range parameter is exclusive.

        Args:
            df (pd.DataFrame): The pandas Dataframe containing the data.
            pagerange (range, optional): The pagerange to include in the table.
            Mutually exclusive with other ranges. Defaults to None.
            postrange (range, optional): The postrange to include in the table.
            Mutually exclusive with other ranges. Defaults to None.
        """
        # Only save data included in ranges
        if pagerange:
            start = pagerange[0]
            end = pagerange[-1]
            selected = df.loc[
                (df["page_num"] >= start) & (df["page_num"] <= end)
            ]
        elif postrange:
            start = postrange[0]
            end = postrange[-1]
            selected = df.loc[start:end]
        else:
            selected = df
        self.df = selected

    @contextmanager
    def change_df(self, df: pd.DataFrame):
        """
        Temporarily switch to a different dataframe.

        :param df: The dataframe to be switched to.
        :type df: pd.DataFrame
        """
        self._df = self.df
        self.df = df
        try:
            yield
        finally:
            self.df = self._df

    @property
    def messages(self) -> int:
        return len(self.df)

    @property
    def words(self) -> int:
        return self.df["word_count"].sum()

    @property
    def first_year(self) -> int:
        return datetime.fromisoformat(
            self.df.head(1).iloc[0]["creation_datetime"]
        ).year

    @property
    def last_year(self) -> int:
        return datetime.fromisoformat(
            self.df.tail(1).iloc[0]["creation_datetime"]
        ).year

    def lookup_id(self, id: str) -> str:
        """
        Lookup a user's name by their id. If None, the user never wrote
        something in that thread.

        :param id: The user id
        :type id: str
        :return: The username
        :rtype: str
        """
        if id == 0:
            return None
        if id not in self.df["author_id"]:
            return None
        return self.df[self.df["author_id"] == id].iloc[0]["author"]

    def get_authors(self) -> list[str]:
        """Get a list of all authors.

        Returns:
            list[str]: The list of authors.
        """
        return self.df["author"].unique().tolist()

    def select_messages_from_author(self, author: str) -> pd.DataFrame:
        return self.df[self.df["author"] == author]

    def get_messages_from_author(self, author: str) -> int:
        """Get the number of messages an author wrote.

        Args:
            author (str): The author's name.

        Returns:
            int: The message count.
        """
        return len(self.select_messages_from_author(author))

    def get_rule_violating_messages_from_author(self, author: str) -> int:
        posts = self.select_messages_from_author(author)
        return len(posts[posts["is_rules_compliant"] == False])  # noqa

    def get_authors_sorted_by_messages(self) -> list[str]:
        """
        Sorts authors by amount of messages, descending.
        """
        authors = self.get_authors()
        authors_to_messages = {}
        for author in authors:
            posts = self.select_messages_from_author(author)
            authors_to_messages[author] = len(posts)
        authors_to_messages = {
            k: v for k, v in sorted(
                authors_to_messages.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        }
        return list(authors_to_messages.keys())

    def get_author_sorted_by_rule_violations_percentage(self) -> list[str]:
        authors = self.get_authors()
        authors_to_rule_violations_percentage = {}
        for author in authors:
            posts = self.get_messages_from_author(author)
            rule_violations = (
                self.get_rule_violating_messages_from_author(author)
            )
            authors_to_rule_violations_percentage[author] = (
                rule_violations / posts
            )
        authors_to_rule_violations_percentage = {
            k: v for k, v in sorted(
                authors_to_rule_violations_percentage.items(),
                key=lambda item: item[1],
                reverse=False,
            )
        }
        return list(authors_to_rule_violations_percentage.keys())

    def select_messages_for_year(self, year: int) -> pd.DataFrame:
        condition = self.df["creation_datetime"].apply(
            lambda x: datetime.fromisoformat(str(x)).year == year
        )
        return self.df[condition]

    def get_authors_sorted_by_words(self) -> list[str]:
        authors = self.get_authors()
        authors_to_words = {}
        for author in authors:
            messages = self.select_messages_from_author(author)
            authors_to_words[author] = messages["word_count"].sum()
        authors_to_words = {
            k: v for k, v in sorted(
                authors_to_words.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        }
        return list(authors_to_words.keys())

    def get_words_from_author(self, author: str) -> int:
        return self.df[self.df["author"] == author]["word_count"].sum()

    def get_used_emojis(self) -> list[str]:
        all_emojis = self.df['emoji_frequency_mapping'].apply(
            lambda d: list(d.keys())
        ).explode()
        unique = all_emojis.unique()
        # Filter weird NaN
        return [i for i in unique if pd.notna(i)]

    def get_emoji_count_for(self, emoji: str) -> int:
        frequencies = self.df['emoji_frequency_mapping'].apply(
            lambda d: d.items()
        ).explode()
        return frequencies[
            frequencies.apply(  # instancecheck for nan
                lambda item: not isinstance(item, float) and emoji == item[0]
            )
        ].apply(itemgetter(1)).sum()

    def get_total_emoji_count(self) -> int:
        return self.df["emoji_count"].sum()


class DataVisualizer:
    """
    A class providing various methods used to visualize
    data in various formats.
    """
    def __init__(self, data_extractor: DataExtractor) -> None:
        self.data_extractor = data_extractor

    def maua1_style_bbtable(self) -> str:
        """
        <printable>
        Constructs a BBCode Table with the authors as Y-axis and the columns
        as X-axis. For an example see https://uwmc.de/p370063.

        Args:

        Returns:
            str: The table using BBCode syntax.
        """
        table = "\
            [TABLE=full][TR][TD]Spieler[/TD][TD]Anzahl Beiträge[/TD]\
            [TD]Anzahl nicht regelkonformer Beiträge[/TD]\
            [TD]Prozentanzahl nicht regelkonformer Beiträge[/TD][/TR]"

        authors_sorted = self.data_extractor.get_authors_sorted_by_messages()
        for author in authors_sorted:
            messages = self.data_extractor.get_messages_from_author(author)
            rules_violating_messages = (
                self.data_extractor.get_rule_violating_messages_from_author(
                    author
                )
            )
            percentage_rules_violating_messages = (
                rules_violating_messages / messages
            )
            table += f"\
                [TR][TD]{author}[/TD]\
                [TD]{messages}[/TD]\
                [TD]{rules_violating_messages}[/TD]\
                [TD]{percentage_rules_violating_messages * 100}%[/TD][/TR]"
        table += "[/TABLE]"
        table = table.replace("  ", "")
        table = table.strip()
        return table

    def rule_violation_bbtable_np(self, n: int = 50) -> str:
        """
        <printable>
        Constructs a BBCode Table containing stats per author, sorted by
        rule violation percentage ascending. Only counts authors with at
        least n messages in the specified range.

        Args:
            n: Messages required to show up in the table

        Returns:
            str: The table using BBCode syntax.
        """
        table = "\
            [TABLE=full][TR][TD]Spieler[/TD][TD]Anzahl Beiträge[/TD]\
            [TD]Anzahl nicht regelkonformer Beiträge[/TD]\
            [TD]Prozentanzahl nicht regelkonformer Beiträge[/TD][/TR]"
        authors_sorted = (
            self.data_extractor.get_author_sorted_by_rule_violations_percentage
        )()
        for author in authors_sorted:
            messages = self.data_extractor.get_messages_from_author(author)
            if messages < n:
                continue
            rules_violating_messages = (
                self.data_extractor.get_rule_violating_messages_from_author(
                    author
                )
            )
            percentage_rules_violating_messages = (
                rules_violating_messages / messages
            )
            table += f"\
                [TR][TD]{author}[/TD]\
                [TD]{messages}[/TD]\
                [TD]{rules_violating_messages}[/TD]\
                [TD]{percentage_rules_violating_messages * 100}%[/TD][/TR]"
        table += "[/TABLE]"
        table = table.replace("  ", "")
        table = table.strip()
        return table

    def top_n_pie(
        self, n: int = 10,
        criterion: Literal["messages", "words"] = "messages",
        radius: float = 1,
    ) -> Figure:
        """
        <plot>
        Creates a pie chart showing the top n players measured by amount of
        messages.

        :param n: Amount of players to show, defaults to 10
        :type n: int, optional
        :param criterion: What criterion to sort by, must be one of messages,
        words
        :type criterion: Literal["messages", "words"]
        :return: The chart
        :rtype: Figure
        """
        if criterion == "messages":
            authors = self.data_extractor.get_authors_sorted_by_messages()[:n]
        else:
            authors = self.data_extractor.get_authors_sorted_by_words()[:n]
        percents = []
        if criterion == "messages":
            total_amount = self.data_extractor.messages
        else:
            total_amount = self.data_extractor.words

        for author in authors:
            if criterion == "messages":
                amount = self.data_extractor.get_messages_from_author(author)
            else:
                amount = self.data_extractor.get_words_from_author(author)
            percents.append(amount / total_amount)
        authors.insert(0, "Rest")
        percents.insert(0, 1 - sum(percents))
        fig, ax = plt.subplots()
        fig.suptitle(f"Top {n} Spieler nach Anzahl " +
                     ("Beiträgen" if criterion == "messages"
                      else "Wörtern"))
        ax.pie(percents, labels=authors, autopct='%1.1f%%', radius=radius)
        return fig

    def yearly_top_n_barh_percent(
        self, n: int = 10,
        criterion: Literal["messages", "words"] = "messages",
    ) -> Figure:
        """
        <plot>
        Creates a horizontal bar chart per year showing the top n players.

        :param n: Amount of top players to show, defaults to 10
        :type n: int, optional
        :param criterion: What criterion to sort by, must be one of messages,
        words
        :type criterion: Literal["messages", "words"]
        :return: The chart
        :rtype: Figure
        """
        total_years = (
            self.data_extractor.last_year - self.data_extractor.first_year + 1
        )
        cols = 2 if total_years > 1 else 1
        rows = math.ceil(total_years / 2)
        fig, axes = plt.subplots(
            nrows=rows,
            ncols=cols,
            layout="constrained",
            figsize=(4 * cols, 3 * rows)
        )
        fig.suptitle(f"Jährliche Top {n} Spieler nach Anzahl " +
                     ("Beiträgen" if criterion == "messages"
                      else "Wörtern"))

        for year, ax in zip(range(
            self.data_extractor.first_year,
            self.data_extractor.last_year + 1,
        ), chain.from_iterable(axes)):
            year_df = self.data_extractor.select_messages_for_year(year)
            with self.data_extractor.change_df(year_df):
                if criterion == "messages":
                    authors = (
                        self.data_extractor.get_authors_sorted_by_messages(
                        )[:n]
                    )
                else:
                    authors = (
                        self.data_extractor.get_authors_sorted_by_words()[:n]
                    )
                percents = []
                if criterion == "messages":
                    total_amount = self.data_extractor.messages
                else:
                    total_amount = self.data_extractor.words
                for author in authors:
                    if criterion == "messages":
                        amount = self.data_extractor.get_messages_from_author(
                            author
                        )
                    else:
                        amount = self.data_extractor.get_words_from_author(
                            author
                        )
                    percents.append(amount / total_amount * 100)
                authors.insert(0, "Rest")
                percents.insert(0, 100 - sum(percents))
                ax: Axes  # type: Axes
                y_pos = np.arange(len(authors))
                ax.barh(y_pos, percents, 0.8, align="edge")
                ax.set_yticks([i + 0.45 for i in y_pos], authors)
                ax.set_title(f"Top {n} {year}")
                ax.set_xlabel(
                    ("Nachrichten" if criterion == "messages" else "Wort") +
                    "anteil in %"
                )
        return fig

    def emojis_pie_top_n(self, n: int = 10, radius: float = 1) -> Figure:
        """
        <plot>
        Creates a pie chart showing the usage percentage of emojis found in the
        dataset.

        :param radius: The pie radius, defaults to 1
        :type radius: float, optional
        :return: The generated pie chart.
        :rtype: Figure
        """
        emojis = self.data_extractor.get_used_emojis()[:n]
        percents = []
        total_emojis = self.data_extractor.get_total_emoji_count()
        for emoji in emojis:
            percents.append(
                total_emojis / self.data_extractor.get_emoji_count_for(emoji)
            )
        fig, ax = plt.subplots()
        fig.suptitle(f"Prozentuale Verwendung der Top {n} Emojis")
        ax.pie(percents, labels=emojis, autopct='%1.1f%%', radius=radius)
        return fig
