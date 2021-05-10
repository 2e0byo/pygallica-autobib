"""Parsers for input data in various formats."""
import bibtexparser
import rispy
from .models import Article, Book, Collection
from typing import Union, List, TextIO, Tuple
from roman import fromRoman, toRoman


class ParsingError(Exception):
    pass


def parse_bibtex(
    bibtex: Union[str, TextIO]
) -> Tuple[List[Union[Article, Book, Collection]], List[str]]:
    try:
        db = bibtexparser.load(bibtex)
        bibtex.seek(0)
        rawlines = (x.strip("\n") for x in bibtex.readlines())
    except Exception:
        try:
            db = bibtexparser.loads(bibtex)
            rawlines = bibtex.split("\n")
        except Exception:
            raise ParsingError("Unable to parse")
    parsed = []
    for record in db.entries:
        pages = record["pages"]
        roman = "i" in pages.lower()
        lower = "i" in pages
        try:
            start, end = pages.split("-")
            startno = fromRoman(start.upper()) if roman else int(start)
            endno = fromRoman(end.upper()) if roman else int(end)
            if not roman and endno < startno:
                endno = int(f"{start[0]}{end}")
            record["pages"] = list(range(startno, endno + 1))
            if roman:
                record["pages"] = [
                    toRoman(x).lower() if lower else toRoman(x) for x in record["pages"]
                ]
        except ValueError:
            record["pages"] = [record["pages"]]

        type_ = record["ENTRYTYPE"]
        mapping = {"article": Article, "book": Book, "collection": Collection}
        if type_ in mapping:
            parsed.append(mapping[type_].parse_obj(record))
        else:
            raise ParsingError("Unsupported type")

    raw = []
    entry = []
    for line in rawlines:
        if line.startswith("@"):
            if entry:
                raw.append([line for line in entry if line.strip()])
                entry = []
        else:
            entry.append(line)

    raw.append([line for line in entry if line.strip()])

    return parsed, raw


def parse_ris(
    ris: Union[str, TextIO]
) -> Tuple[List[Union[Article, Book, Collection]], List]:
    try:
        db = rispy.load(ris)
        ris.seek(0)
        rawlines = [x.strip("\n") for x in ris.readlines()]
    except Exception:
        try:
            db = rispy.loads(ris)
            rawlines = ris.split("\n")
        except Exception:
            raise ParsingError("Unable to parse")
    parsed = []
    for record in db:
        record["pages"] = list(
            range(int(record["start_page"]), int(record["end_page"]) + 1)
        )
        record["author"] = "and".join(record["authors"])
        record["journaltitle"] = record["secondary_title"]
        mapping = {"JOUR": Article, "BOOK": Book, "COLL": Collection}
        type_ = record["type_of_reference"]
        if type_ in mapping:
            parsed.append(mapping[type_].parse_obj(record))
        else:
            raise ParsingError("Unsupported type")

    raw = []
    entry = []
    for line in rawlines:
        if not line.strip():
            if entry:
                raw.append(entry)
                entry = []
        else:
            entry.append(line)

    if entry:
        raw.append(entry)

    return parsed, raw
