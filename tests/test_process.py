from gallica_autobib.process import (
    extract_image,
    ExtractionError,
    get_crop_bounds,
    deanomalise,
    detect_spine,
    prepare_img,
)
import pytest
from PyPDF4 import PdfFileReader
from pathlib import Path
from collections import namedtuple
from tempfile import TemporaryDirectory
from devtools import debug
from PIL import Image, ImageOps


def test_extract_no_image():
    with pytest.raises(ExtractionError, match=".*No image.*"):
        reader = PdfFileReader("tests/test_process/test-blank.pdf")
        page1 = reader.getPage(0)
        extract_image(page1)


ImgTest = namedtuple("ImgTest", ("testfile", "type"))

test_image_pdf = [
    ImgTest(Path("tests/test_process/test5.pdf"), "png"),
    ImgTest(Path("tests/test_process/test2.pdf"), "jpg"),
    ImgTest(Path("tests/test_process/test3.pdf"), "jp2"),
    # ImgTest(Path("tests/test_process/test4.pdf"), "tiff"),
]


@pytest.mark.parametrize("img_test", test_image_pdf)
def test_extract_image(img_test, image_regression):
    with img_test.testfile.open("rb") as f:
        reader = PdfFileReader(f)
        page1 = reader.getPage(0)
        img, type_ = extract_image(page1)
        assert type_ == img_test.type
    with TemporaryDirectory() as tmpdir:
        outf = Path(f"{tmpdir}/test.{type_}")
        img.save(str(outf))
        with outf.open("rb") as f:
            image_regression.check(f.read())


def test_deanomalise():
    assert deanomalise([0, 1, 1, 5]) == 1
    assert deanomalise([1, 1, 1]) == 1
    assert deanomalise([12]) == 12


def test_detect_spine():
    inf = "tests/test_process/lh.jpg"
    img = Image.open(inf)
    img = prepare_img(img, 128)
    assert detect_spine(img).lh_page
    inf = "tests/test_process/rh.jpg"
    img = Image.open(inf)
    img = prepare_img(img, 128)
    assert not detect_spine(img).lh_page


def test_crop_bounds_lh():
    inf = "tests/test_process/lh.jpg"
    img = Image.open(inf)
    assert get_crop_bounds(img) == (46, 149, 786, 1393)


def test_crop_bounds_rh():
    inf = "tests/test_process/rh.jpg"
    img = Image.open(inf)
    assert get_crop_bounds(img) == (161, 160, 898, 1394)
