import xml.dom.minidom

import pytest

from webapp import house


@pytest.mark.parametrize("key", sorted(house.ROOM_ART))
def test_every_room_drawing_is_valid_svg(key):
    svg = house.ROOM_ART[key]()
    document = xml.dom.minidom.parseString(svg)
    assert document.documentElement.tagName == "svg" and document.documentElement.getAttribute("viewBox") == "0 0 300 170"


def test_there_is_an_illustration_for_each_of_the_four_rooms():
    assert set(house.ROOM_ART) == {"learn", "test", "second", "stay"}
