import xml.dom.minidom

import pytest

from webapp import house


@pytest.mark.parametrize("key", sorted(house.ROOM_ART))
def test_every_room_drawing_is_valid_svg(key):
    svg = house.ROOM_ART[key]()
    document = xml.dom.minidom.parseString(svg)
    assert document.documentElement.tagName == "svg" and document.documentElement.getAttribute("viewBox") == "0 0 300 170"


@pytest.mark.parametrize("name", ["ROOF", "TREE", "BUSH", "MAILBOX", "CLOUD"])
def test_garden_and_roof_drawings_are_valid_svg(name):
    xml.dom.minidom.parseString(getattr(house, name))


def test_the_house_has_the_four_rooms():
    assert set(house.ROOM_ART) == {"learn", "test", "second", "stay"}


def test_roof_shingle_lines_are_not_filled():
    """Regression: unfilled paths default to black, which painted the whole roof black."""
    assert 'fill="none"' in house.ROOF.split("<g", 1)[1]
