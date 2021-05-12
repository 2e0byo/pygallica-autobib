import pickle
import pytest
from pathlib import Path
from devtools import debug
from gallica_autobib.gallipy import Resource
from gallica_autobib.models import Article, Journal, Book, Collection
from gallica_autobib.query import GallicaResource, Query
from gallica_autobib.gallipy.ark import ArkParsingError


@pytest.fixture(scope="session")
def pages():
    inf = Path("tests/test_gallica_resource/pages.pickle")
    with inf.open("rb") as f:
        yield pickle.load(f)


@pytest.fixture
def gallica_resource():
    target = Article(
        journaltitle="La vie spirituelle",
        pages=list(range(135, 158)),
        title="Pour lire saint Augustin",
        author="Daniélou",
        year=1930,
    )
    source = Journal(
        year=[
            1919,
            1920,
            1921,
            1922,
            1923,
            1924,
            1925,
            1926,
            1927,
            1928,
            1929,
            1930,
            1931,
            1932,
            1933,
            1934,
            1935,
            1936,
            1937,
            1938,
            1939,
            1940,
            1941,
            1942,
            1943,
            1944,
            1945,
        ],
        publisher="Le Cerf (Paris)",
        ark="http://catalogue.bnf.fr/ark:/12148/cb34406663m",
        journaltitle="La Vie spirituelle, ascétique et mystique",
        number=None,
        volume=None,
    )
    yield GallicaResource(target, source)


def test_get_issue(gallica_resource):
    assert gallica_resource.get_issue()


def test_ark(gallica_resource):
    ark = gallica_resource.ark
    assert str(ark) == "ark:/12148/bpt6k9735634r"


def test_by_vol(gallica_resource):
    gallica_resource.target.volume = 24
    ark = gallica_resource.ark
    assert str(ark) == "ark:/12148/bpt6k9735634r"


def test_resource(gallica_resource):
    res = gallica_resource.resource
    assert isinstance(res, Resource)


def test_pnos(gallica_resource):
    assert 141 == gallica_resource.start_p
    assert 163 == gallica_resource.end_p


def test_generate_blocks(gallica_resource):
    expected = [(0, 5), (5, 5), (10, 5), (15, 5), (20, 1)]
    res = list(gallica_resource._generate_blocks(0, 20, 5))


def test_generate_short_block(gallica_resource):
    expected = [(0, 4)]
    res = list(gallica_resource._generate_blocks(0, 3, 100))
    assert res == expected


def test_download_pdf(gallica_resource, file_regression, tmp_path, check_pdfs):
    gallica_resource.target.pages = gallica_resource.target.pages[:3]

    outf = tmp_path / "test.pdf"
    gallica_resource.download_pdf(outf)
    with outf.open("rb") as f:
        file_regression.check(
            f.read(), binary=True, extension=".pdf", check_fn=check_pdfs
        )


@pytest.mark.xfail
def test_book():
    book = Book(title="t", author="s", editor="e")
    res = GallicaResource(book, book)


@pytest.mark.xfail
def test_journal():
    journal = Journal(journaltitle="j", year="1930")
    res = GallicaResource(journal, journal)


@pytest.mark.xfail
def test_collection():
    coll = Collection(title="t", author="a")
    res = GallicaResource(coll, coll)


def test_invalid_ark():
    source = Journal(journaltitle="j", year="1930", ark="notavalidark")
    target = Article(
        journaltitle="La vie spirituelle",
        pages=list(range(135, 158)),
        title="Pour lire saint Augustin",
        author="Daniélou",
        year=1930,
    )
    with pytest.raises(ArkParsingError):
        GallicaResource(target, source)


def test_repr(gallica_resource, data_regression):
    data_regression.check(str(gallica_resource))


candidates = [
    [
        Article(
            journaltitle="La Vie spirituelle",
            author="Jean Daniélou",
            pages=list(range(547, 552)),
            volume=7,
            year=1923,
            title="Ascèse et péché originel",
        ),
        dict(ark="ark:/12148/bpt6k97356214"),
    ]
]


@pytest.mark.parametrize("candidate, params", candidates)
def test_real_queries_volume_number(candidate, params):
    source = Query(candidate).run().candidate
    gallica_resource = GallicaResource(candidate, source)
    assert str(gallica_resource.ark) == params["ark"]


@pytest.mark.parametrize("candidate, params", candidates)
def test_real_queries_no_volume_number(candidate, params):
    source = Query(candidate).run().candidate
    gallica_resource = GallicaResource(candidate, source)
    gallica_resource.consider_volume_number = False
    assert str(gallica_resource.ark) == params["ark"]


def test_parse_description_range(gallica_resource):
    desc = "1922/10 (A4,T7,N37)-1923/03 (A4,T7,N42)."
    resp = gallica_resource.parse_description(desc)
    assert resp["year"] == [1922, 1923]
    assert resp["volume"] == 7
    assert resp["number"] == list(range(37, 43))


def test_parse_description_range_everywhere(gallica_resource):
    desc = "1922/10 (A4,T7,N37)-1923/03 (A4,T8,N42)."
    resp = gallica_resource.parse_description(desc)
    assert resp["year"] == [1922, 1923]
    assert resp["volume"] == [7, 8]
    assert resp["number"] == list(range(37, 43))


def test_parse_description(gallica_resource):
    desc = "1922/10 (A4,T7,N37)."
    resp = gallica_resource.parse_description(desc)
    assert resp["year"] == 1922
    assert resp["volume"] == 7
    assert resp["number"] == 37


def test_parse_no_description(gallica_resource):
    desc = ""
    resp = gallica_resource.parse_description(desc)
    assert all(v is None for k, v in resp.items())


def test_parse_partial_description(gallica_resource):
    desc = "1922/10 (T7)."
    resp = gallica_resource.parse_description(desc)
    assert resp["year"] == 1922
    assert resp["volume"] == 7
    assert resp["number"] is None


def test_physical_pno(gallica_resource, pages):
    resp = gallica_resource.get_physical_pno("10", pages=pages)
    assert resp == "16"


def test_last_pno(gallica_resource, pages):
    resp = gallica_resource.get_last_pno(pages)
    assert resp == "676"
