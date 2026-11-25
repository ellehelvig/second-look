"""Generate the banner and social-preview images for this repository.

Matches the style of the profile banner in ellehelvig/ellehelvig. Writes SVG banners
(light, dark, and narrow-screen versions), plus a PNG social preview for upload in
the repository's settings. Needs Pillow for text measurement and PNG output.

Usage, from the repository root: python scripts/generate_brand_assets.py . secondlook"""

import sys
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

THEMES = {
    "dark": dict(bg="#070910", surface="#0d111c", text="#f5f7fb", muted="#a4aec2", violet="#a99fff",
                 cyan="#61ddec", border="#596780", grid="#182132"),
    "light": dict(bg="#f5f7fb", surface="#ffffff", text="#172033", muted="#4b5870", violet="#5140b5",
                  cyan="#086779", border="#73809b", grid="#e3e8f2"),
}
SANS = "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Consolas, monospace"
FONTS = {(False, 400): "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
         (False, 600): "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
         (False, 650): "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
         (True, 400): "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"}

PROJECTS = {
    "plos": dict(
        slug="plos",
        eyebrow="ELLE HELVIG / OFFICE OF THE CPO",
        title=["People Leadership OS"], title_mobile=["People Leadership", "OS"],
        sub=["How a Chief of Staff runs the Office of the CPO on GitHub."],
        sub_mobile=["How a Chief of Staff runs", "the Office of the CPO on GitHub."],
        chips=["ISSUES", "WEEKLY BRIEF", "DECISIONS"],
        status="FICTIONAL COMPANY / COPILOT DRAFTS, A PERSON DECIDES",
        foot="Every claim in the brief cites its source.",
        alt="People Leadership OS. How a Chief of Staff runs the Office of the CPO on GitHub: issues, a weekly brief, and decision records.",
    ),
    "secondlook": dict(
        slug="second-look",
        eyebrow="ELLE HELVIG / HR AI GOVERNANCE",
        title=["Second Look"], title_mobile=["Second Look"],
        sub=["When an automated decision goes against someone."],
        sub_mobile=["When an automated decision", "goes against someone."],
        chips=["NOTICE", "EXPLANATION", "CORRECTION", "HUMAN REVIEW"],
        status="REFERENCE DESIGN / FICTIONAL DATA",
        foot="Notice, explanation, correction, and a different reviewer.",
        alt="Second Look. When an automated decision goes against someone: notice, explanation, correction, and human review by a different person.",
    ),
}


class Canvas:
    """Collects drawing calls and writes both SVG and PNG."""

    def __init__(self, w, h, theme, alt):
        self.w, self.h, self.t, self.alt, self.ops = w, h, THEMES[theme], alt, []

    def text(self, x, y, value, size, color, mono=False, weight=400):
        self.ops.append(("text", x, y, value, size, self.t[color], mono, weight))

    def chip(self, x, y, label, color="cyan"):
        width = self.text_width(label, 19, True) + 32
        self.ops.append(("chip", x, y, width, 44))
        self.text(x + 16, y + 28, label, 19, color, True)
        return width

    @staticmethod
    def text_width(value, size, mono=False, weight=400):
        return ImageFont.truetype(FONTS[(mono, weight)], size).getlength(value)

    def svg(self):
        t, w, h = self.t, self.w, self.h
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(self.alt, quote=True)}">',
               f'<title>{escape(self.alt)}</title><defs><linearGradient id="accent"><stop stop-color="{t["violet"]}"/><stop offset="1" stop-color="{t["cyan"]}"/></linearGradient>',
               f'<pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="{t["grid"]}"/></pattern></defs>',
               f'<rect width="{w}" height="{h}" rx="16" fill="{t["bg"]}"/>',
               f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16" fill="url(#grid)"/>',
               f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16" fill="none" stroke="{t["border"]}"/>',
               '<rect x="32" y="28" width="80" height="4" rx="2" fill="url(#accent)"/>']
        for op in self.ops:
            if op[0] == "text":
                _, x, y, value, size, color, mono, weight = op
                out.append(f'<text x="{x}" y="{y}" font-family="{MONO if mono else SANS}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(value)}</text>')
            else:
                _, x, y, cw, ch = op
                out.append(f'<rect x="{x}" y="{y}" width="{cw:.0f}" height="{ch}" rx="8" fill="{t["surface"]}" stroke="{t["border"]}"/>')
        out.append("</svg>\n")
        return "".join(out)

    def png(self, path, scale=1):
        t, s = self.t, scale
        img = Image.new("RGB", (self.w * s, self.h * s), t["bg"])
        d = ImageDraw.Draw(img)
        for gx in range(0, self.w, 48):
            d.line([(gx * s, 0), (gx * s, self.h * s)], fill=t["grid"], width=s)
        for gy in range(0, self.h, 48):
            d.line([(0, gy * s), (self.w * s, gy * s)], fill=t["grid"], width=s)
        d.rounded_rectangle([s, s, (self.w - 1) * s, (self.h - 1) * s], radius=16 * s, outline=t["border"], width=s)
        for i in range(80):
            frac = i / 79
            a, b = t["violet"], t["cyan"]
            c = tuple(round(int(a[k:k + 2], 16) * (1 - frac) + int(b[k:k + 2], 16) * frac) for k in (1, 3, 5))
            d.line([((32 + i) * s, 28 * s), ((32 + i) * s, 31 * s)], fill=c, width=s)
        for op in self.ops:
            if op[0] == "chip":
                _, x, y, cw, ch = op
                d.rounded_rectangle([x * s, y * s, (x + cw) * s, (y + ch) * s], radius=8 * s, fill=t["surface"], outline=t["border"], width=s)
        for op in self.ops:
            if op[0] == "text":
                _, x, y, value, size, color, mono, weight = op
                d.text((x * s, y * s), value, font=ImageFont.truetype(FONTS[(mono, weight)], size * s), fill=color, anchor="ls")
        img.save(path, optimize=True)


def banner(p, theme, mobile):
    w, h, x = (720, 500, 40) if mobile else (1280, 440, 64)
    c = Canvas(w, h, theme, p["alt"])
    c.text(x, 88, p["eyebrow"], 20, "violet", True)
    y = 181
    for line in (p["title_mobile"] if mobile else p["title"]):
        c.text(x, y, line, 66 if mobile else 80, "text", weight=650)
        y += 72
    y += -10 if not mobile else -14
    for line in (p["sub_mobile"] if mobile else p["sub"]):
        c.text(x, y, line, 32 if mobile else 36, "muted")
        y += 44
    cy, cx = y + 28, x
    for label in p["chips"]:
        cx += c.chip(cx, cy, label) + 18
    return c


def social(p):
    c = Canvas(1280, 640, "dark", p["alt"])
    c.text(64, 100, p["eyebrow"], 22, "violet", True)
    c.text(64, 224, " ".join(p["title"]), 72, "text", weight=650)
    c.text(64, 330, p["sub"][0], 34, "muted")
    cx = 64
    for label in p["chips"]:
        cx += c.chip(cx, 384, label) + 18
    c.text(64, 520, p["status"], 23, "cyan", True)
    c.text(64, 570, p["foot"], 30, "violet")
    return c


if __name__ == "__main__":
    out, key = Path(sys.argv[1]), sys.argv[2]
    p = PROJECTS[key]
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        for mobile in (False, True):
            name = f'{p["slug"]}-{"mobile-" if mobile else ""}{theme}'
            c = banner(p, theme, mobile)
            (out / "assets" / f"{name}.svg").write_text(c.svg())
    s = social(p)
    (out / "assets" / "social-preview.svg").write_text(s.svg())
    s.png(out / "assets" / "social-preview.png")
    print("ok", key)
