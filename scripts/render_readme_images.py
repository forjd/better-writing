"""Render docs/before-after.gif and docs/social-preview.png for the README.

Usage: python3 scripts/render_readme_images.py FONTS_DIR [OUT_DIR]

Needs Pillow and IBM Plex from google/fonts (OFL) in FONTS_DIR:

    base=https://github.com/google/fonts/raw/main/ofl
    for f in ibmplexmono/IBMPlexMono-Regular.ttf ibmplexmono/IBMPlexMono-SemiBold.ttf \
             ibmplexserif/IBMPlexSerif-Regular.ttf ibmplexserif/IBMPlexSerif-SemiBold.ttf \
             ibmplexserif/IBMPlexSerif-Italic.ttf; do curl -sSfLO "$base/$f"; done
    curl -sSfL -o PlexSans.ttf "$base/ibmplexsans/IBMPlexSans%5Bwdth,wght%5D.ttf"

OUT_DIR defaults to docs/. Keep AFTER in step with
evals/examples/launch-email.md.
"""
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "docs"
OUT.mkdir(parents=True, exist_ok=True)


def sans(size, weight="Regular"):
    f = ImageFont.truetype(str(FONTS / "PlexSans.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def serif(size, weight="Regular"):
    return ImageFont.truetype(str(FONTS / f"IBMPlexSerif-{weight}.ttf"), size)


def mono(size, weight="Regular"):
    return ImageFont.truetype(str(FONTS / f"IBMPlexMono-{weight}.ttf"), size)


BG = "#f4f1ea"
CARD = "#fffdf8"
BORDER = "#e3ded3"
INK = "#1c1b19"
MUTED = "#6b665c"
CUT = "#b42318"
CUT_BG = "#fde8e6"
KEEP_BG = "#d9f2e3"
KEEP_INK = "#0f5132"
ACCENT = "#2563eb"

BEFORE = (
    "[s:I hope this email finds you well! We're thrilled to announce the launch of our "
    "groundbreaking new] [f:analytics dashboard], which goes live on [f:Monday 15 June]. "
    "[s:This isn't just an update — it's a game-changer designed to transform your workflow.] "
    "The dashboard replaces the [f:weekly CSV export], and data now refreshes [f:every hour] "
    "instead of [f:every seven days], [s:empowering you to unlock deeper insights] across "
    "[f:teams, projects, and date ranges]. [s:To get started on this exciting journey, simply] "
    "navigate to the [f:Reports tab] after logging in. [s:Exciting times lie ahead!]"
)
AFTER = (
    "Our new [f:analytics dashboard] goes live on [f:Monday 15 June]. It replaces the "
    "[f:weekly CSV export]. Data refreshes [f:every hour] instead of [f:every seven days], "
    "and you can view it across [f:teams, projects, and date ranges]. To start using it, "
    "log in and open the [f:Reports tab]."
)


def tokens(text):
    """Split marked-up text into (word, style) pairs; style is '', 's' or 'f'."""
    out = []
    for m in re.finditer(r"\[(s|f):([^\]]+)\]|([^\[]+)", text):
        style, body = (m.group(1), m.group(2)) if m.group(1) else ("", m.group(3))
        glued = style == "" and not body.startswith(" ")
        for word in body.split(" "):
            if word:
                # Punctuation right after a marked span attaches without a space.
                out.append((word, style, glued and bool(out)))
            glued = False
    return out


def layout(toks, font, width, line_h):
    """Greedy wrap; returns list of (x, y, word, style) and total height."""
    space = font.getlength(" ")
    x = y = 0
    placed = []
    for word, style, glued in toks:
        w = font.getlength(word)
        if glued and x:
            x -= space
        if x and x + w > width:
            x, y = 0, y + line_h
        placed.append((x, y, word, style, w))
        x += w + space
    return placed, y + line_h


def draw_text(draw, placed, ox, oy, font, line_h, mode):
    """mode: 'plain', 'marked' (before with cuts), 'after' (facts only)."""
    space = font.getlength(" ")
    asc, desc = font.getmetrics()
    # Backgrounds first so they sit under the text, joined across spaces.
    for i, (x, y, word, style, w) in enumerate(placed):
        nxt = placed[i + 1] if i + 1 < len(placed) else None
        joined = nxt and nxt[3] == style and nxt[1] == y
        ext = space if joined else 0
        top, bot = oy + y + 4, oy + y + asc + desc + 2
        if mode != "plain" and style == "f":
            draw.rectangle([ox + x - 2, top, ox + x + w + ext + 2, bot], fill=KEEP_BG)
        if mode == "marked" and style == "s":
            draw.rectangle([ox + x - 2, top, ox + x + w + ext + 2, bot], fill=CUT_BG)
    for i, (x, y, word, style, w) in enumerate(placed):
        fill = INK
        if mode != "plain" and style == "f":
            fill = KEEP_INK
        if mode == "marked" and style == "s":
            fill = CUT
        draw.text((ox + x, oy + y), word, font=font, fill=fill)
        if mode == "marked" and style == "s":
            nxt = placed[i + 1] if i + 1 < len(placed) else None
            joined = nxt and nxt[3] == "s" and nxt[1] == y
            mid = oy + y + asc * 0.62
            draw.line([ox + x - 1, mid, ox + x + w + (space if joined else 0) + 1, mid],
                      fill=CUT, width=2)


def pill(draw, x, y, text, font, fg, bg):
    w = font.getlength(text)
    draw.rounded_rectangle([x, y, x + w + 28, y + 38], radius=19, fill=bg)
    draw.text((x + 14, y + 5), text, font=font, fill=fg)
    return x + w + 28


def gif():
    W, PAD, CPAD = 1200, 40, 48
    body = serif(27)
    line_h = 44
    text_w = W - 2 * PAD - 2 * CPAD
    before, bh = layout(tokens(BEFORE), body, text_w, line_h)
    after, ah = layout(tokens(AFTER), body, text_w, line_h)
    head_h, foot_h = 96, 72
    text_h = max(bh, ah)
    H = PAD * 2 + head_h + text_h + foot_h + 24
    label = sans(20, "SemiBold")
    small = sans(19)

    def frame(mode, word_count):
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([PAD, PAD, W - PAD, H - PAD], radius=18, fill=CARD,
                            outline=BORDER, width=2)
        x = PAD + CPAD
        y = PAD + 36
        if mode == "after":
            pill(d, x, y, "After", label, "#ffffff", KEEP_INK)
            caption = f"{word_count} words. Every fact kept."
        elif mode == "marked":
            pill(d, x, y, "Auditing", label, "#ffffff", CUT)
            caption = "Red is cut. Green is a fact that must survive."
        else:
            pill(d, x, y, "Before", label, "#ffffff", INK)
            caption = f"{word_count} words of launch email."
        d.text((W - PAD - CPAD, y + 7), caption, font=small, fill=MUTED, anchor="ra")
        placed = after if mode == "after" else before
        draw_text(d, placed, x, PAD + head_h + 8, body, line_h, mode)
        fy = H - PAD - 52
        d.line([x, fy - 14, W - PAD - CPAD, fy - 14], fill=BORDER, width=2)
        d.text((x, fy), "better-writing", font=mono(19, "SemiBold"), fill=INK)
        d.text((W - PAD - CPAD, fy), "github.com/forjd/better-writing",
               font=mono(19), fill=MUTED, anchor="ra")
        return im

    count = lambda s: len(re.sub(r"\[[sf]:|\]", "", s).split())
    frames = [frame("plain", count(BEFORE)), frame("marked", 0), frame("after", count(AFTER))]
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    pal[0].save(OUT / "before-after.gif", save_all=True, append_images=pal[1:],
                duration=[3200, 4200, 4600], loop=0, optimize=True, disposal=1)


def social():
    W, H = 1280, 640
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    x = 88
    d.text((x, 92), "Better Writing", font=sans(76, "Bold"), fill=INK)
    d.text((x, 190), "An agent skill for prose that sounds clear, specific, and human.",
           font=sans(30), fill=MUTED)
    # Mini before/after card.
    cy = 262
    d.rounded_rectangle([x, cy, W - x, cy + 214], radius=16, fill=CARD, outline=BORDER, width=2)
    body = serif(28)
    ix = x + 36
    before = "We're thrilled to announce our groundbreaking new dashboard!"
    w = body.getlength(before)
    d.text((ix, cy + 38), before, font=body, fill=CUT)
    asc, _ = body.getmetrics()
    d.line([ix - 2, cy + 38 + asc * 0.62, ix + w + 2, cy + 38 + asc * 0.62], fill=CUT, width=3)
    d.text((ix, cy + 88), "↓", font=sans(30, "SemiBold"), fill=MUTED)
    after = "The new analytics dashboard goes live on Monday 15 June."
    d.rectangle([ix - 4, cy + 142, ix + body.getlength(after) + 4, cy + 180], fill=KEEP_BG)
    d.text((ix, cy + 138), after, font=body, fill=KEEP_INK)
    # Points.
    pts = ["Keeps your voice", "Never invents facts", "Ships with evals"]
    px = x
    for p in pts:
        f = sans(24, "SemiBold")
        d.ellipse([px, 529, px + 12, 541], fill=ACCENT)
        d.text((px + 22, 518), p, font=f, fill=INK)
        px += 22 + f.getlength(p) + 48
    d.text((W - x, 522), "forjd/better-writing", font=mono(22), fill=MUTED, anchor="ra")
    im.save(OUT / "social-preview.png", optimize=True)


gif()
social()
print("ok")
