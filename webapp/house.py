"""The 2D drawing of the house: a roof, four illustrated rooms, and the garden.

Everything is inline SVG built from plain strings (no image files), so it scales cleanly and follows the theme.
Each room is drawn on a 300 x 170 canvas with the floor at y = 130; furniture sits on that line.
"""
from __future__ import annotations

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 170" preserveAspectRatio="xMidYMax slice" class="room-art">'
WOOD, WOOD_DARK, BRASS = "#C8AE86", "#8C6A43", "#B8893A"


def _room_shell(wall: str, wainscot: str) -> str:
    """Wall, wainscoting, wooden floor with planks, and skirting board."""
    return (f'<rect width="300" height="170" fill="{wall}"/><rect y="94" width="300" height="36" fill="{wainscot}"/>'
            f'<path d="M0 94H300" stroke="#fff" stroke-opacity=".6" stroke-width="2"/>'
            f'<rect y="130" width="300" height="40" fill="{WOOD}"/><path d="M0 143H300M0 156H300" stroke="#B89A70"/>'
            f'<path d="M40 130V143M120 143V156M200 130V143M260 143V156" stroke="#B89A70"/>'
            f'<rect y="126" width="300" height="5" fill="{WOOD_DARK}"/>')


def _books(x: float, y_bottom: float, specs: list[tuple[float, float, str]]) -> str:
    """A row of books standing on y_bottom: (width, height, colour) each."""
    out, cursor = [], x
    for width, height, colour in specs:
        out.append(f'<rect x="{cursor:.1f}" y="{y_bottom - height:.1f}" width="{width}" height="{height}" rx="1" fill="{colour}"/>'
                   f'<rect x="{cursor + 1:.1f}" y="{y_bottom - height + 4:.1f}" width="{max(width - 2, 1)}" height="2" fill="#fff" opacity=".45"/>')
        cursor += width + 0.8
    return "".join(out)


def learn_room() -> str:
    books1 = _books(23, 57, [(7, 26, "#A93A4F"), (6, 22, "#35506B"), (8, 28, "#B8893A"), (6, 24, "#2F7D5E"), (7, 27, "#5B4A7A"),
                             (6, 21, "#A93A4F"), (8, 25, "#35506B"), (6, 28, "#B8893A"), (7, 23, "#2F7D5E"), (6, 26, "#8C6A43")])
    books2 = _books(23, 89, [(8, 26, "#35506B"), (6, 29, "#A93A4F"), (7, 23, "#B8893A"), (9, 27, "#2F5D50"), (6, 24, "#5B4A7A"),
                             (7, 28, "#35506B"), (6, 22, "#A93A4F"), (8, 26, "#B8893A")])
    return (HEAD + _room_shell("#E8EEF5", "#D6E0EB") +
            # window with a view and curtains
            f'<rect x="214" y="26" width="66" height="60" rx="3" fill="{BRASS}"/><rect x="219" y="31" width="56" height="50" fill="#BFDAEE"/>'
            f'<path d="M247 31V81M219 56H275" stroke="{BRASS}" stroke-width="3"/><circle cx="232" cy="44" r="5" fill="#fff" opacity=".8"/>'
            f'<path d="M219 81 q14 -22 28 -8 q14 -16 28 8Z" fill="#8FB58A" opacity=".85"/>'
            # bookshelf
            f'<rect x="16" y="20" width="96" height="108" rx="3" fill="{WOOD_DARK}"/><rect x="21" y="25" width="86" height="98" fill="#6B4F2F"/>'
            f'<path d="M21 58H107M21 90H107" stroke="{WOOD_DARK}" stroke-width="4"/>{books1}{books2}'
            f'<rect x="26" y="96" width="30" height="24" rx="2" fill="#F6F1E7"/><path d="M30 104H52M30 110H48" stroke="#B8893A" stroke-width="2"/>'
            f'<circle cx="86" cy="108" r="13" fill="#7FA6C9"/><path d="M73 108H99M86 95V121" stroke="#fff" stroke-opacity=".6"/>'
            # desk, open book, lamp, plant
            f'<rect x="124" y="98" width="100" height="8" rx="2" fill="{WOOD_DARK}"/><rect x="130" y="106" width="6" height="21" fill="#6B4F2F"/>'
            f'<rect x="212" y="106" width="6" height="21" fill="#6B4F2F"/><rect x="132" y="108" width="80" height="14" rx="2" fill="#7A5A38"/>'
            f'<path d="M146 97 Q158 90 170 94 L170 99 Q158 96 146 101Z" fill="#fff"/><path d="M194 97 Q182 90 170 94 L170 99 Q182 96 194 101Z" fill="#F4EEDF"/>'
            f'<path d="M150 96H165M150 98.5H165M175 96H190M175 98.5H190" stroke="#9AA7B5" stroke-width=".8"/>'
            f'<ellipse cx="206" cy="97" rx="9" ry="2.5" fill="#6B4F2F"/><path d="M206 96V76L196 70" stroke="{BRASS}" stroke-width="2.5" fill="none"/>'
            f'<path d="M188 74 L200 64 L212 74Z" fill="{BRASS}"/><path d="M190 76 L172 98 H210Z" fill="#FFE7A3" opacity=".28"/>'
            f'<rect x="108" y="90" width="12" height="9" rx="2" fill="#B8893A"/><path d="M114 90 q-8 -10 -4 -16 M114 90 q8 -9 5 -17" stroke="#3E7B57" stroke-width="2.5" fill="none"/>'
            '</svg>')


def test_room() -> str:
    return (HEAD + _room_shell("#E3EFEA", "#CFE3DA") +
            # wall clock
            '<circle cx="58" cy="50" r="24" fill="#2F5D50"/><circle cx="58" cy="50" r="20" fill="#FFFDF8"/>'
            '<path d="M58 33V37M58 63V67M41 50H45M71 50H75" stroke="#2F5D50" stroke-width="2.5"/>'
            '<path d="M58 50V38M58 50L68 56" stroke="#1B2433" stroke-width="2.6" stroke-linecap="round"/><circle cx="58" cy="50" r="2.4" fill="#B8893A"/>'
            # blackboard
            f'<rect x="132" y="24" width="150" height="70" rx="3" fill="{BRASS}"/><rect x="137" y="29" width="140" height="60" fill="#2D4A41"/>'
            '<text x="170" y="72" font-family="Georgia,serif" font-size="38" font-weight="700" fill="#F6F1E7">A+</text>'
            '<path d="M236 50 l9 11 l20 -26" stroke="#9FE0B5" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M146 38H190M146 82H176" stroke="#F6F1E7" stroke-opacity=".5" stroke-width="2"/>'
            f'<rect x="150" y="93" width="120" height="3" fill="{WOOD_DARK}"/><rect x="236" y="87" width="18" height="6" rx="2" fill="#F6F1E7"/>'
            # desk with exam paper and pencil, chair
            f'<rect x="32" y="102" width="104" height="8" rx="2" fill="{WOOD_DARK}"/><rect x="38" y="110" width="6" height="18" fill="#6B4F2F"/>'
            '<rect x="124" y="110" width="6" height="18" fill="#6B4F2F"/>'
            '<rect x="52" y="86" width="42" height="17" rx="1" fill="#fff" transform="rotate(-6 73 95)"/>'
            '<path d="M57 91H88M57 96H84" stroke="#9AA7B5" stroke-width="1.2" transform="rotate(-6 73 95)"/>'
            '<path d="M80 90 l4 5 l9 -11" stroke="#2F6B4F" stroke-width="2.4" fill="none" stroke-linecap="round" transform="rotate(-6 73 95)"/>'
            f'<rect x="102" y="98" width="26" height="3.2" rx="1" fill="#F0B83A" transform="rotate(-12 115 99)"/><path d="M127 96 l5 2 l-5 1Z" fill="#E7C7A2"/>'
            '<rect x="152" y="104" width="34" height="5" rx="2" fill="#7B2D3B"/><rect x="154" y="80" width="6" height="26" rx="2" fill="#7B2D3B"/>'
            '<rect x="154" y="80" width="30" height="5" rx="2" fill="#7B2D3B"/><rect x="156" y="109" width="4" height="19" fill="#4A1C25"/><rect x="178" y="109" width="4" height="19" fill="#4A1C25"/>'
            '<g transform="translate(240 100)"><rect x="0" y="0" width="30" height="28" rx="3" fill="#2F5D50"/><rect x="3" y="-4" width="24" height="6" rx="2" fill="#fff"/>'
            '<rect x="4" y="8" width="22" height="2.6" fill="#fff" opacity=".7"/><rect x="4" y="14" width="22" height="2.6" fill="#fff" opacity=".7"/></g>'
            '</svg>')


def second_chance_room() -> str:
    return (HEAD + _room_shell("#F6E6DF", "#EBD3C9") +
            # big framed "try again" arrow
            f'<rect x="30" y="18" width="88" height="70" rx="3" fill="{BRASS}"/><rect x="35" y="23" width="78" height="60" fill="#FFF7F0"/>'
            '<path d="M95 41 A22 22 0 1 0 98 62" stroke="#A4553D" stroke-width="7" fill="none" stroke-linecap="round"/>'
            '<path d="M86 34 L104 40 L92 54Z" fill="#A4553D"/>'
            # window
            f'<rect x="206" y="24" width="68" height="62" rx="3" fill="{BRASS}"/><rect x="211" y="29" width="58" height="52" fill="#F3D6C4"/>'
            f'<path d="M240 29V81M211 55H269" stroke="{BRASS}" stroke-width="3"/>'
            '<path d="M211 81 q16 -20 29 -8 q14 -14 29 8Z" fill="#C97A5E" opacity=".7"/>'
            # rug, armchair
            '<ellipse cx="150" cy="150" rx="86" ry="11" fill="#A4553D" opacity=".28"/><ellipse cx="150" cy="150" rx="64" ry="7.5" fill="#F6E6DF" opacity=".6"/>'
            '<rect x="102" y="84" width="62" height="46" rx="14" fill="#A4553D"/><rect x="92" y="100" width="20" height="30" rx="9" fill="#8F4631"/>'
            '<rect x="154" y="100" width="20" height="30" rx="9" fill="#8F4631"/><rect x="110" y="104" width="46" height="22" rx="7" fill="#B8654C"/>'
            '<rect x="100" y="128" width="5" height="8" fill="#4A2A1F"/><rect x="161" y="128" width="5" height="8" fill="#4A2A1F"/>'
            f'<rect x="118" y="92" width="24" height="14" rx="5" fill="{BRASS}"/>'
            # side table with lamp and notebook
            f'<rect x="188" y="104" width="44" height="6" rx="2" fill="{WOOD_DARK}"/><rect x="192" y="110" width="5" height="18" fill="#6B4F2F"/><rect x="224" y="110" width="5" height="18" fill="#6B4F2F"/>'
            f'<rect x="194" y="98" width="20" height="6" rx="1" fill="#2C3E5C"/><rect x="194" y="98" width="3" height="6" fill="{BRASS}"/>'
            f'<path d="M222 104V86" stroke="{BRASS}" stroke-width="2.4"/><path d="M212 90 L222 78 L232 90Z" fill="#E8C98A"/><path d="M213 92 L205 104 H239 L231 92Z" fill="#FFE7A3" opacity=".3"/>'
            # plant
            '<path d="M268 126 l-3 -22 h22 l-3 22Z" fill="#8C6A43"/><path d="M276 104 q-14 -14 -8 -30 M276 104 q12 -14 10 -32 M276 104 q0 -20 2 -34" stroke="#3E7B57" stroke-width="4" fill="none" stroke-linecap="round"/>'
            '</svg>')


def living_room() -> str:
    return (HEAD + _room_shell("#F6EBD3", "#EBDDBE") +
            # picture frames
            f'<rect x="28" y="22" width="44" height="34" rx="2" fill="{BRASS}"/><rect x="32" y="26" width="36" height="26" fill="#DDE8D6"/><path d="M32 52 l10 -12 l8 8 l8 -10 l10 14Z" fill="#6E9A74"/>'
            f'<rect x="82" y="30" width="26" height="32" rx="2" fill="{BRASS}"/><rect x="85" y="33" width="20" height="26" fill="#F3E2D0"/><circle cx="95" cy="44" r="6" fill="#C9886B"/>'
            # window with curtains
            f'<rect x="206" y="22" width="70" height="66" rx="3" fill="{BRASS}"/><rect x="211" y="27" width="60" height="56" fill="#CFE3F2"/><path d="M241 27V83M211 55H271" stroke="{BRASS}" stroke-width="3"/>'
            '<path d="M198 18 q10 36 4 76 h22 q-8 -40 -2 -76Z" fill="#7B2D3B"/><path d="M284 18 q-10 36 -4 76 h-22 q8 -40 2 -76Z" fill="#7B2D3B"/>'
            '<rect x="194" y="14" width="96" height="5" rx="2" fill="#4A1C25"/>'
            # rug and sofa
            '<ellipse cx="124" cy="152" rx="104" ry="12" fill="#2C3E5C" opacity=".22"/><ellipse cx="124" cy="152" rx="80" ry="8" fill="#B8893A" opacity=".25"/>'
            '<rect x="44" y="78" width="164" height="52" rx="14" fill="#2C3E5C"/><rect x="32" y="96" width="28" height="36" rx="12" fill="#243450"/>'
            '<rect x="192" y="96" width="28" height="36" rx="12" fill="#243450"/><rect x="56" y="100" width="136" height="26" rx="8" fill="#35507A"/>'
            '<rect x="50" y="130" width="6" height="8" fill="#14202F"/><rect x="196" y="130" width="6" height="8" fill="#14202F"/>'
            f'<rect x="66" y="86" width="30" height="22" rx="7" fill="{BRASS}"/><rect x="104" y="88" width="28" height="20" rx="7" fill="#E7DCC4"/><rect x="154" y="86" width="30" height="22" rx="7" fill="#A93A4F"/>'
            # coffee table with the diary
            f'<rect x="226" y="112" width="58" height="7" rx="2" fill="{WOOD_DARK}"/><rect x="232" y="119" width="5" height="11" fill="#6B4F2F"/><rect x="272" y="119" width="5" height="11" fill="#6B4F2F"/>'
            f'<rect x="236" y="98" width="40" height="15" rx="2" fill="#2F5D50"/><rect x="236" y="98" width="5" height="15" fill="{BRASS}"/>'
            f'<rect x="246" y="102" width="22" height="3" fill="{BRASS}"/><rect x="246" y="107" width="14" height="2" fill="{BRASS}" opacity=".7"/>'
            # floor lamp
            f'<rect x="14" y="52" width="4" height="76" fill="{BRASS}"/><path d="M6 54 L16 36 L26 54Z" fill="#E8C98A"/><ellipse cx="16" cy="128" rx="9" ry="2.5" fill="{BRASS}"/>'
            '</svg>')


ROOM_ART = {"learn": learn_room, "test": test_room, "second": second_chance_room, "stay": living_room}

ROOF = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 170" preserveAspectRatio="none" class="roof">'
        '<polygon points="10,170 500,12 990,170" fill="#7B2D3B"/>'
        '<polygon points="10,170 500,12 990,170" fill="none" stroke="#4A1C25" stroke-width="6" stroke-linejoin="round"/>'
        '<g stroke="#5E2230" stroke-width="2.2" opacity=".75" fill="none">'
        '<path d="M64 150 L500 52 L936 150M118 128 L500 92 L882 128M172 106 L500 68 L828 106M226 84 L500 30 L774 84"/></g>'
        '<circle cx="500" cy="98" r="22" fill="#FFFDF8" stroke="#B8893A" stroke-width="6"/>'
        '<path d="M500 80V116M482 98H518" stroke="#B8893A" stroke-width="3"/></svg>')

TREE = ('<svg viewBox="0 0 120 150" class="deco-tree" xmlns="http://www.w3.org/2000/svg"><rect x="54" y="84" width="14" height="62" fill="#6B4F2F"/>'
        '<circle cx="60" cy="56" r="42" fill="#5E8F62"/><circle cx="36" cy="72" r="28" fill="#6FA070"/><circle cx="86" cy="70" r="30" fill="#4E7D54"/>'
        '<circle cx="58" cy="38" r="22" fill="#7DB07C" opacity=".8"/></svg>')

BUSH = ('<svg viewBox="0 0 120 50" class="deco-bush" xmlns="http://www.w3.org/2000/svg"><circle cx="30" cy="30" r="22" fill="#5E8F62"/>'
        '<circle cx="62" cy="26" r="26" fill="#4E7D54"/><circle cx="94" cy="32" r="20" fill="#6FA070"/>'
        '<circle cx="44" cy="22" r="3" fill="#E7B1B8"/><circle cx="76" cy="18" r="3" fill="#E7B1B8"/><circle cx="100" cy="28" r="3" fill="#F2D488"/></svg>')

MAILBOX = ('<svg viewBox="0 0 80 120" xmlns="http://www.w3.org/2000/svg"><rect x="36" y="54" width="8" height="64" fill="#6B4F2F"/>'
           '<path d="M10 54 V34 a30 22 0 0 1 60 0 V54Z" fill="#2C3E5C"/><rect x="10" y="50" width="60" height="6" fill="#1B2A41"/>'
           '<rect x="62" y="22" width="5" height="30" fill="#7B2D3B"/><rect x="62" y="22" width="16" height="9" rx="1" fill="#7B2D3B"/>'
           '<rect x="22" y="38" width="30" height="5" rx="1" fill="#B8893A"/></svg>')

CLOUD = '<svg viewBox="0 0 160 60" xmlns="http://www.w3.org/2000/svg"><path d="M20 52 a18 18 0 0 1 4 -35 a26 26 0 0 1 50 -6 a22 22 0 0 1 36 12 a16 16 0 0 1 28 18 a14 14 0 0 1 -6 11Z" fill="currentColor"/></svg>'
