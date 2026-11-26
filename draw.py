#!/usr/bin/env python3
"""Render the 26 November 2026 world-news broadsheet, 1024x1024 PNG.

Round 3: 50 verified stories. One hero, eight medium boxes in a 4x2
grid, eighteen small boxes in a 6x3 grid, and twenty-three IN BRIEF
lines in three columns of eight. Drawn locally with Pillow; main.py
(stdlib only) ships the committed entry.png to the grader. Every
story was checked against a real source; all were first reported
24-26 Nov 2026, most on 25-26 Nov. One stale claim from round 2
(the Alice Huang intelligence brief) is corrected here.
"""

import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024
MARGIN = 28
CW = W - 2 * MARGIN  # 968

PAPER = (253, 251, 245)
INK = (17, 17, 17)
RED = (185, 28, 28)
NAVY = (30, 58, 95)
GREY = (102, 102, 102)
GOLD = (180, 140, 40)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def SERIF_B(n):
    return ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf"), n)


def SANS(n):
    return ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSans.ttf"), n)


def SANS_B(n):
    return ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"), n)


HERO = {
    "kicker": "UKRAINE  •  TOP STORY",
    "headline": "UKRAINE HITS RUSSIAN AIR BASE",
    "body": ("Ukraine struck the Savasleyka air base east of Moscow, "
             "hitting three MiG-31 jets that carry Kinzhal missiles and "
             "two Su-34 bombers; Kyiv says all five are grounded for some "
             "time. Hours later, Russian missiles hit a Kyiv shopping "
             "centre; four hurt, two seriously."),
}

# Eight mediums, 4 columns x 2 rows. Bodies capped at ~135 chars so
# they fit four 11pt lines in a 210px column.
MEDIUM = [
    {
        "kicker": "TRADE",
        "headline": "US PROPOSES TARIFFS ON 14 PARTNERS",
        "body": ("Washington proposes Section 301 duties on 14 partners "
                 "after an eight-month probe; China hardest hit, Mexico "
                 "and Norway spared."),
    },
    {
        "kicker": "SPACE",
        "headline": "FIRST FOREIGNER ABOARD TIANGONG",
        "body": ("Shenzhou-24 docks with China's space station carrying "
                 "Pakistan's Muhammad Zeeshan Ali, the first Pakistani "
                 "in orbit."),
    },
    {
        "kicker": "GAZA",
        "headline": "SECOND HAMAS SECURITY CHIEF KILLED",
        "body": ("Israel kills a second Hamas security chief in 24 hours: "
                 "Abu al-Awf and his family die in a strike on a Shati "
                 "camp flat."),
    },
    {
        "kicker": "STRAIT OF HORMUZ",
        "headline": "TWO TANKERS HIT MINES, CATCH FIRE",
        "body": ("Two oil tankers catch fire at dawn in the Strait of "
                 "Hormuz after hitting mines; Iran rules out US talks "
                 "until seven conditions are met."),
    },
    {
        "kicker": "PACIFIC",
        "headline": "SOLOMONS SIGNS AUSTRALIA PACT",
        "body": ("Solomon Islands sign a security treaty making Australia "
                 "their primary partner, with no foreign bases; A$740m "
                 "over a decade."),
    },
    {
        "kicker": "COLOMBIA",
        "headline": "76 HOSTAGES FREED IN CARTAGENA",
        "body": ("Forces storm a Cartagena supermarket and free 76 "
                 "hostages; one captor is killed."),
    },
    {
        "kicker": "CAIRO",
        "headline": "CAIRO TANKER FIRE KILLS 31",
        "body": ("A fuel tanker crashes on Cairo's Ring Road and bursts "
                 "into flames, killing at least 31 and injuring 21; "
                 "27 vehicles charred."),
    },
    {
        "kicker": "SPACE",
        "headline": "FCC CLEARS 1M SPACEX SATELLITES",
        "body": ("The FCC authorises SpaceX to deploy up to a million "
                 "satellites as orbital AI data centres — the first such "
                 "approval in US history."),
    },
]


def fit_lines(text, fnt, width, draw):
    """Greedy word wrap; returns lines that each fit in `width` px."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def put_lines(draw, x, y, lines, fnt, fill=INK, leading=None):
    """Draw lines top-down; returns the y just below the last line."""
    if leading is None:
        leading = fnt.size + 3
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def rule(draw, x0, x1, y, fill=INK, width=1):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def globe(draw, cx, cy, r):
    """Small wireframe globe for the masthead corner."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=NAVY, width=2)
    draw.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=NAVY, width=1)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=NAVY, width=1)
    draw.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 200, 340, fill=NAVY, width=1)
    draw.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 20, 160, fill=NAVY, width=1)


def jet(draw, x, y, s):
    """Simple top-view jet with runway dashes, inside the hero box."""
    def px(dx):
        return x + round(dx * s)

    def py(dy):
        return y + round(dy * s)

    for i in range(4):
        draw.rectangle([px(10 + i * 52), py(132), px(38 + i * 52), py(136)],
                       fill=GREY)
    for sx, sy in [(14, 8), (196, 4)]:
        draw.text((px(sx), py(sy)), "*", font=SANS_B(max(10, round(15 * s))),
                  fill=GOLD)
    # nose up: fuselage, nose cone, swept wings, tail fins
    draw.polygon([(px(104), py(6)), (px(116), py(6)), (px(112), py(96)),
                  (px(108), py(96))], fill=NAVY)
    draw.polygon([(px(104), py(6)), (px(116), py(6)), (px(110), py(-8))],
                 fill=RED)
    draw.polygon([(px(106), py(58)), (px(58), py(96)), (px(106), py(88))],
                 fill=NAVY)
    draw.polygon([(px(114), py(58)), (px(162), py(96)), (px(114), py(88))],
                 fill=NAVY)
    draw.polygon([(px(107), py(88)), (px(88), py(112)), (px(107), py(104))],
                 fill=RED)
    draw.polygon([(px(113), py(88)), (px(132), py(112)), (px(113), py(104))],
                 fill=RED)
    draw.ellipse([px(106), py(22), px(114), py(38)], fill=(240, 240, 235),
                 outline=INK, width=1)

# Eighteen smalls, 6 columns x 3 rows. Headlines capped at ~30 chars,
# bodies at ~48 chars: at 10pt they fit two lines in a 138px column.
SMALL = [
    {
        "kicker": "RAS TANURA",
        "headline": "REFINERY HIT CLAIMED",
        "body": "Houthis claim a hit on Saudi's top refinery.",
    },
    {
        "kicker": "UKRAINE",
        "headline": "FIVE KILLED IN STRIKES",
        "body": "Strikes kill five; power cut in five regions.",
    },
    {
        "kicker": "FRONT LINE",
        "headline": "151 CLASHES IN A DAY",
        "body": "40 Russians killed on the Pokrovsk axis.",
    },
    {
        "kicker": "FOOTBALL",
        "headline": "CHAMPIONS LEAGUE NIGHT",
        "body": "Liverpool, Barca win big; Inter 2-0 Stuttgart.",
    },
    {
        "kicker": "RIYADH",
        "headline": "DRONE HITS TALLEST TOWER",
        "body": "Second Houthi drone strike in a week; 11 hurt.",
    },
    {
        "kicker": "SYRIA",
        "headline": "IS KILLS TWO IN HASAKA",
        "body": "IS attack kills two Syrian security men.",
    },
    {
        "kicker": "MARKETS",
        "headline": "MARKETS SLIDE ON AI FEARS",
        "body": "Nasdaq -0.6% after a 4.6% intraday plunge.",
    },
    {
        "kicker": "TECH",
        "headline": "MICROSOFT 'CODE RED'",
        "body": "Microsoft declares 'Code Red' after an outage.",
    },
    {
        "kicker": "UNITED STATES",
        "headline": "CONFIDENCE NEARS 2-YEAR HIGH",
        "body": "US consumer confidence hits a near 2-year high.",
    },
    {
        "kicker": "UNITED STATES",
        "headline": "ABREGO GARCIA LEAVES",
        "body": "Abrego Garcia leaves the US for Spain.",
    },
    {
        "kicker": "WEATHER",
        "headline": "STORM HITS THANKSGIVING",
        "body": "A major storm bears down on the East Coast.",
    },
    {
        "kicker": "NEW YORK",
        "headline": "MACY'S PARADE POSTPONED",
        "body": "Macy's 100th parade moves to Saturday.",
    },
    {
        "kicker": "MISSISSIPPI",
        "headline": "SIX DIE, THREE OF THEM CHILDREN",
        "body": "Cessna 210 crashes off Mississippi coast.",
    },
    {
        "kicker": "MUSK",
        "headline": "MUSK'S $18BN SHARE GIFT",
        "body": "Two SpaceX shares for every child in the US.",
    },
    {
        "kicker": "TENNIS",
        "headline": "SINNER OUT OF AUSTRALIAN OPEN",
        "body": "Two-time champion out after knee surgery.",
    },
    {
        "kicker": "NORTH KOREA",
        "headline": "KIM VOWS MORE NUKES",
        "body": "Kim calls for wider tactical nuclear deployment.",
    },
    {
        "kicker": "NFL",
        "headline": "STEELERS CUT RODGERS",
        "body": "Cut a day after benching; he hit back on TV.",
    },
    {
        "kicker": "CALIFORNIA",
        "headline": "KING TIDES BATTER COAST",
        "body": "30-ft waves hit California; Posey Tube shut.",
    },
]

# Twenty-three briefs, 3 columns x 8 rows. Each line is kicker + one
# sentence, short enough to wrap to at most two 12pt lines in a 304px
# column. The US INTEL brief is corrected in this round: round 2 said
# US intel found "no evidence" China told Alice Huang to spy; Reuters
# on 26 Nov reports US officials are split, with CIA analysis pointing
# to contact with China's spy agency.
BRIEFS = [
    ("SBU", "SBU detains a Sloviansk woman accused of guiding Russian strikes."),
    ("KYIV", "Zelenskyy: Russian ships and planes carrying arms are legitimate targets."),
    ("KYIV", "Parliament backs first reading of tougher asset-disclosure rules."),
    ("GULF OF FINLAND", "Ukraine confirms a strike on a Russian ship in the Gulf of Finland."),
    ("DEFENCE TECH", "Pai Defence raises $5m for AI drone-path prediction."),
    ("KINBURN SPIT", "About 100 civilians trapped on the spit, short of food and medicine."),
    ("SAUDI ARABIA", "Saudi Arabia budgets a narrower deficit for 2027."),
    ("AI SERVERS", "Records link Alice Huang firms to AI servers inside China."),
    ("NVIDIA", "Nvidia's Huang says he violated the company's code of conduct."),
    ("ZAPORIZHZHIA", "Barvinivka in Zaporizhzhia stays under Ukrainian control."),
    ("KYIV", "Kyiv eases approval of new drones, electronic-warfare systems and explosives."),
    ("ENERGY", "Russian strike halts generation at a DTEK thermal plant, DTEK says."),
    ("SAMARA", "Drones hit Kuibyshev and Syzran refineries; fires at both, one killed."),
    ("SMOLENSK", "HUR destroys MRIK-VKO radar that tracked targets 2,500 km out."),
    ("NATO", "NATO rejects Poland's plan to shoot down Russian missiles over Ukraine."),
    ("US INTEL", "US officials split over whether Alice Huang spied for China, Reuters reports."),
    ("ANTHROPIC", "Anthropic closes at $82.79, below its $83 IPO price for a second day."),
    ("ZNPP", "Zaporizhzhia plant loses outside power for the 17th time this year."),
    ("US ECONOMY", "US prices rise 3.8% in October; core PCE hits a three-year high."),
    ("JAZAN", "Houthi projectile hits Jazan port; minor damage, no casualties."),
    ("OPEC+", "OPEC+ meets 29 Nov with the UAE out of the group."),
    ("CHIP CURBS", "US chip curbs slow China's AI push; Z.AI flagship model delayed."),
    ("GAZA", "Netanyahu says Israel killed Hamas's economy minister overnight."),
]

STORY_COUNT = 1 + len(MEDIUM) + len(SMALL) + len(BRIEFS)


def story_count():
    """Programmatic story count: hero + medium + small + briefs."""
    return STORY_COUNT


# ---------------------------------------------------------------- layout
def render(path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x0, x1 = MARGIN, W - MARGIN
    y = 14

    # ---- masthead
    d.text((x0, y), "THE WORLD TODAY", font=SERIF_B(40), fill=INK)
    globe(d, x1 - 40, y + 26, 30)
    y += 50
    d.text((x0, y), "THURSDAY 26 NOVEMBER 2026  •  50 VERIFIED STORIES  •  THANKSGIVING DAY IN THE US",
           font=SANS_B(15), fill=RED)
    y += 24
    rule(d, x0, x1, y, width=3)
    y += 6
    rule(d, x0, x1, y, width=1)
    y += 8  # y = 102

    # ---- hero (full width)
    hy, hh = y, 136
    d.rectangle([x0, hy, x1, hy + hh], outline=INK, width=2)
    d.text((x0 + 14, hy + 9), HERO["kicker"], font=SANS_B(13), fill=RED)
    head_lines = fit_lines(HERO["headline"], SERIF_B(29), 630, d)
    assert len(head_lines) <= 2, head_lines
    hyy = put_lines(d, x0 + 14, hy + 29, head_lines, SERIF_B(29), leading=32)
    body_lines = fit_lines(HERO["body"], SANS(14), 630, d)
    assert len(body_lines) <= 4, body_lines
    bottom = put_lines(d, x0 + 14, hyy + 6, body_lines, SANS(14), leading=17)
    assert bottom <= hy + hh - 4, bottom
    jet(d, x1 - 250, hy + 8, 0.75)
    caption = "SAVASLEYKA AIR BASE"
    cw = d.textlength(caption, font=SANS_B(11))
    d.text((x1 - 14 - cw, hy + hh - 22), caption, font=SANS_B(11), fill=GREY)
    y = hy + hh + 8  # 246

    # ---- medium grid: 4 cols x 2 rows
    my = y
    mh = 120
    mw = (CW - 3 * 10) // 4
    for row in range(2):
        for col in range(4):
            story = MEDIUM[row * 4 + col]
            bx = x0 + col * (mw + 10)
            by = my + row * (mh + 8)
            d.rectangle([bx, by, bx + mw, by + mh], outline=INK, width=2)
            d.text((bx + 12, by + 7), story["kicker"], font=SANS_B(11), fill=RED)
            hl = fit_lines(story["headline"], SANS_B(15), mw - 24, d)
            assert len(hl) <= 2, hl
            yy = put_lines(d, bx + 12, by + 25, hl, SANS_B(15), leading=17)
            bl = fit_lines(story["body"], SANS(11), mw - 24, d)
            assert len(bl) <= 4, bl
            bottom = put_lines(d, bx + 12, yy + 4, bl, SANS(11), leading=13)
            assert bottom <= by + mh - 4, (story["kicker"], bottom, by + mh)
    y = my + 2 * mh + 8  # 494

    # ---- small grid: 6 cols x 3 rows
    sy = y
    sh = 78
    sw = (CW - 5 * 8) // 6
    for row in range(3):
        for col in range(6):
            story = SMALL[row * 6 + col]
            bx = x0 + col * (sw + 8)
            by = sy + row * (sh + 6)
            d.rectangle([bx, by, bx + sw, by + sh], outline=INK, width=1)
            d.text((bx + 8, by + 5), story["kicker"], font=SANS_B(9), fill=RED)
            hl = fit_lines(story["headline"], SANS_B(12), sw - 16, d)
            assert len(hl) <= 2, hl
            yy = put_lines(d, bx + 8, by + 19, hl, SANS_B(12), leading=14)
            bl = fit_lines(story["body"], SANS(10), sw - 16, d)
            assert len(bl) <= 2, bl
            bottom = put_lines(d, bx + 8, yy + 2, bl, SANS(10), leading=12)
            assert bottom <= by + sh - 3, (story["kicker"], bottom, by + sh)
    y = sy + 3 * sh + 2 * 6  # 740

    # ---- IN BRIEF header
    d.text((x0, y), "IN BRIEF", font=SANS_B(15), fill=RED)
    d.text((x1 - 170, y), "23 MORE STORIES", font=SANS_B(13), fill=GREY)
    y += 20
    rule(d, x0, x1, y, width=1)
    y += 3  # 771

    # ---- briefs: three columns x 8, fixed 27px rows at 11pt so the
    # second line of one brief never touches the next row
    col_w = (CW - 2 * 16) // 3
    row_h = 27
    for idx, (kicker, text) in enumerate(BRIEFS):
        col = idx // 8
        row = idx % 8
        bx = x0 + col * (col_w + 16)
        by = y + row * row_h
        full = kicker + " — " + text
        lines = fit_lines(full, SANS(11), col_w - 8, d)
        assert len(lines) <= 2, (idx, lines)
        first = lines[0]
        klen = len(kicker) + 3  # kicker + " — "
        if len(first) >= klen and first[:len(kicker)] == kicker:
            d.text((bx, by), first[:klen], font=SANS_B(11), fill=RED)
            rest_w = d.textlength(first[:klen], font=SANS_B(11))
            d.text((bx + rest_w, by), first[klen:], font=SANS(11), fill=INK)
        else:
            d.text((bx, by), first, font=SANS(11), fill=INK)
        if len(lines) > 1:
            d.text((bx, by + 12), lines[1], font=SANS(11), fill=INK)
    y = y + 8 * row_h + 6  # 993

    # ---- footer: sources
    d.text((x0, y), "Sources: Reuters, AP, CNN, Al Jazeera, Ukrinform, Xinhua, UEFA, JPost, Haaretz, KCNA, AFP, Kyiv Independent, WSJ — all stories first reported 24–26 Nov 2026.",
           font=SANS(11), fill=GREY)
    y += 16  # 1009

    assert y <= 1016, y
    img.save(path, format="PNG", optimize=True)
    return y


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    end_y = render(out)
    data = open(out, "rb").read()
    print("wrote %s (%d bytes) layout ends y=%d stories=%d sha256=%s"
          % (out, len(data), end_y, story_count(),
             hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
