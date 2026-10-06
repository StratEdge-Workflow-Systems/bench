#!/usr/bin/env python3
"""45-second GuardRoute film. 1920x1080. Worked example, same facts as the Bench receipt."""

from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
DURATION = 45.0
N = int(FPS * DURATION)

BG = (7, 11, 20)
CARD = (16, 24, 38)
CARD_EDGE = (36, 48, 68)
TEXT = (244, 247, 251)
MUTED = (154, 166, 182)
DIM = (92, 104, 122)
AMBER = (245, 185, 66)
AMBER_DIM = (120, 86, 28)
EMERALD = (61, 220, 151)
RED = (255, 122, 122)

OUT = Path(__file__).resolve().parent / "guardroute-45.mp4"
POSTER = Path(__file__).resolve().parent / "guardroute-45.jpg"

FONT_REG = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def clamp(t: float) -> float:
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def ease(t: float) -> float:
    t = clamp(t)
    return 1 - (1 - t) ** 3


def fade(t: float, a: float, b: float) -> float:
    if t < a:
        return 0.0
    if t > b:
        return 1.0
    return ease((t - a) / (b - a))


def fonts() -> dict[str, ImageFont.FreeTypeFont]:
    def reg(size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(FONT_REG, size, index=0)

    def bold(size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(FONT_BOLD, size)

    return {
        "kicker": bold(22),
        "hero": bold(84),
        "hero2": bold(64),
        "amount": bold(92),
        "name": bold(48),
        "verdict": bold(54),
        "body": reg(32),
        "small": reg(24),
        "tiny": reg(20),
        "check": reg(28),
        "chip": bold(22),
    }


F = fonts()


def text_w(font: ImageFont.FreeTypeFont, text: str) -> int:
    b = font.getbbox(text)
    return b[2] - b[0]


def text_h(font: ImageFont.FreeTypeFont, text: str) -> int:
    b = font.getbbox(text)
    return b[3] - b[1]


def make_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    px = img.load()
    for y in range(H):
        k = y / (H - 1)
        r = int(BG[0] + (18 - BG[0]) * k * 0.35)
        g = int(BG[1] + (22 - BG[1]) * k * 0.2)
        b = int(BG[2] + (36 - BG[2]) * k)
        for x in range(0, W, 2):
            px[x, y] = (r, g, b)
            if x + 1 < W:
                px[x + 1, y] = (r, g, b)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((520, -180, 1500, 520), fill=(42, 28, 8))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    return Image.blend(img, glow, 0.55)


BASE = make_bg()


class Frame:
    def __init__(self) -> None:
        self.img = BASE.copy()
        self.over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.over)

    def finish(self) -> Image.Image:
        return Image.alpha_composite(self.img.convert("RGBA"), self.over).convert("RGB")


def blit_text(
    fr: Frame,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    alpha: float,
    anchor: str = "lt",
) -> None:
    if alpha <= 0.01 or not text:
        return
    color = (*fill, int(255 * clamp(alpha)))
    if anchor == "mm":
        tw, th = text_w(font, text), text_h(font, text)
        xy = (int(xy[0] - tw / 2), int(xy[1] - th / 2))
    fr.d.text(xy, text, font=font, fill=color)


def round_card(
    fr: Frame,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    alpha: float,
    radius: int = 28,
) -> None:
    if alpha <= 0.01:
        return
    a = int(255 * clamp(alpha))
    fr.d.rounded_rectangle(box, radius=radius, fill=(*fill, a), outline=(*outline, a), width=2)


def bar(fr: Frame, t: float) -> None:
    fr.d.rectangle((0, H - 6, W, H), fill=(20, 26, 36, 255))
    fr.d.rectangle((0, H - 6, int(W * clamp(t / DURATION)), H), fill=(*AMBER, 255))


def brand(fr: Frame) -> None:
    fr.d.text((80, 48), "GUARDROUTE", font=F["kicker"], fill=(*AMBER, 255))
    fr.d.text(
        (W - 80 - text_w(F["tiny"], "Worked example"), 52),
        "Worked example",
        font=F["tiny"],
        fill=(*DIM, 255),
    )


def scene_open(fr: Frame, t: float) -> None:
    brand(fr)
    a1 = fade(t, 0.2, 1.1)
    a2 = fade(t, 0.8, 1.8)
    a3 = fade(t, 1.6, 2.6)
    blit_text(fr, (W // 2, 390), "One field.", F["hero"], TEXT, a1, "mm")
    blit_text(fr, (W // 2, 500), "The payment stops.", F["hero"], TEXT, a2, "mm")
    blit_text(
        fr,
        (W // 2, 640),
        "Same amount. Same authority. A different payee.",
        F["body"],
        MUTED,
        a3,
        "mm",
    )


def scene_request(fr: Frame, t: float) -> None:
    brand(fr)
    local = t - 5.0
    blit_text(fr, (120, 150), "The request", F["small"], MUTED, fade(local, 0.0, 0.4))
    blit_text(fr, (120, 200), "$4,200", F["amount"], TEXT, fade(local, 0.15, 0.7))
    blit_text(fr, (120, 320), "Approved vendor invoice  ·  PAY-100", F["body"], MUTED, fade(local, 0.4, 0.9))
    rows = [
        ("Authority", "On file"),
        ("Evidence", "Complete"),
        ("Limit", "$25,000"),
        ("Amount", "Inside the limit"),
    ]
    for i, (k, v) in enumerate(rows):
        a = fade(local, 0.7 + i * 0.28, 1.2 + i * 0.28)
        y = 430 + i * 88
        round_card(fr, (120, y, 980, y + 72), CARD, CARD_EDGE, a, 18)
        blit_text(fr, (148, y + 20), k, F["check"], DIM, a)
        blit_text(fr, (420, y + 18), v, F["check"], TEXT, a)


def scene_allow(fr: Frame, t: float) -> None:
    brand(fr)
    local = t - 12.0
    blit_text(fr, (120, 150), "Known payee", F["small"], EMERALD, fade(local, 0.0, 0.35))
    blit_text(fr, (120, 200), "Northline Custodial", F["name"], TEXT, fade(local, 0.15, 0.6))
    blit_text(fr, (120, 270), "Already on the roll.  $4,200.", F["body"], MUTED, fade(local, 0.4, 0.9))
    checks = [
        ("Identity", "PASS"),
        ("Limit", "PASS"),
        ("Evidence", "PASS"),
        ("Counterparty", "PASS"),
        ("Adversary", "QUIET"),
    ]
    for i, (k, v) in enumerate(checks):
        a = fade(local, 0.7 + i * 0.22, 1.15 + i * 0.22)
        y = 370 + i * 78
        round_card(fr, (120, y, 1100, y + 64), CARD, (28, 70, 58), a, 16)
        blit_text(fr, (148, y + 16), k, F["check"], MUTED, a)
        blit_text(fr, (520, y + 16), v, F["check"], EMERALD, a)
    a = fade(local, 2.4, 3.1)
    round_card(fr, (1280, 420, 1760, 620), (12, 40, 32), EMERALD, a, 24)
    blit_text(fr, (1520, 500), "ALLOW", F["verdict"], EMERALD, a, "mm")
    blit_text(fr, (1520, 660), "It proceeds.", F["body"], MUTED, fade(local, 3.0, 3.6), "mm")


def scene_change(fr: Frame, t: float) -> None:
    brand(fr)
    local = t - 18.0
    blit_text(fr, (W // 2, 400), "One fact changes.", F["hero2"], TEXT, fade(local, 0.1, 0.7), "mm")
    blit_text(fr, (W // 2, 510), "The payee.", F["hero"], AMBER, fade(local, 0.8, 1.5), "mm")
    blit_text(
        fr,
        (W // 2, 650),
        "Amount, authority, and evidence stay the same.",
        F["body"],
        MUTED,
        fade(local, 1.6, 2.3),
        "mm",
    )


def scene_escalate(fr: Frame, t: float) -> None:
    brand(fr)
    local = t - 23.0
    blit_text(fr, (120, 140), "New payee", F["small"], AMBER, fade(local, 0.0, 0.3))
    blit_text(fr, (120, 186), "Harbor Relay LLC", F["name"], TEXT, fade(local, 0.15, 0.55))
    blit_text(fr, (120, 258), "Not on the roll.  Still $4,200.", F["body"], MUTED, fade(local, 0.4, 0.85))
    checks = [
        ("Identity", "PASS", EMERALD),
        ("Limit", "PASS", EMERALD),
        ("Evidence", "PASS", EMERALD),
        ("Counterparty", "FAIL", RED),
        ("Adversary", "PRESSURE", AMBER),
    ]
    for i, (k, v, color) in enumerate(checks):
        a = fade(local, 0.8 + i * 0.35, 1.3 + i * 0.35)
        y = 340 + i * 86
        edge = RED if v == "FAIL" else AMBER if v == "PRESSURE" else (28, 70, 58)
        round_card(fr, (120, y, 1180, y + 70), CARD, edge, a, 16)
        blit_text(fr, (148, y + 18), k, F["check"], MUTED, a)
        blit_text(fr, (560, y + 18), v, F["check"], color, a)
    a = fade(local, 3.2, 4.0)
    round_card(fr, (1280, 430, 1780, 680), (48, 32, 8), AMBER, a, 24)
    blit_text(fr, (1530, 520), "ESCALATE", F["verdict"], AMBER, a, "mm")
    blit_text(fr, (1530, 730), "Stopped before it runs.", F["small"], MUTED, fade(local, 4.2, 4.9), "mm")


def scene_split(fr: Frame, t: float) -> None:
    brand(fr)
    local = t - 32.0
    blit_text(fr, (W // 2, 160), "Same payment.  $4,200.", F["body"], TEXT, fade(local, 0.05, 0.45), "mm")
    a = fade(local, 0.3, 0.9)
    round_card(fr, (140, 240, 900, 820), CARD, (28, 90, 70), a, 28)
    round_card(fr, (1020, 240, 1780, 820), CARD, AMBER, a, 28)
    blit_text(fr, (180, 300), "Known payee", F["small"], EMERALD, a)
    blit_text(fr, (180, 360), "Northline Custodial", F["name"], TEXT, a)
    blit_text(fr, (180, 470), "$4,200", F["hero2"], TEXT, fade(local, 0.6, 1.1))
    blit_text(fr, (180, 640), "ALLOW", F["verdict"], EMERALD, fade(local, 1.0, 1.6))
    blit_text(fr, (1060, 300), "New payee", F["small"], AMBER, a)
    blit_text(fr, (1060, 360), "Harbor Relay LLC", F["name"], TEXT, a)
    blit_text(fr, (1060, 470), "$4,200", F["hero2"], TEXT, fade(local, 0.8, 1.3))
    blit_text(fr, (1060, 640), "ESCALATE", F["verdict"], AMBER, fade(local, 1.3, 1.9))
    blit_text(
        fr,
        (W // 2, 900),
        "The payee changed. ALLOW becomes ESCALATE.",
        F["body"],
        MUTED,
        fade(local, 2.0, 2.6),
        "mm",
    )


def scene_close(fr: Frame, t: float) -> None:
    brand(fr)
    local = t - 39.0
    blit_text(fr, (120, 160), "Before the money moves.", F["hero2"], TEXT, fade(local, 0.1, 0.7))
    outcomes = [
        "ALLOW",
        "ALLOW WITH LIMITS",
        "REQUIRE APPROVAL",
        "ESCALATE",
        "HOLD",
        "BLOCK",
    ]
    for i, name in enumerate(outcomes):
        a = fade(local, 0.6 + i * 0.18, 1.05 + i * 0.18)
        col = i % 2
        row = i // 2
        x = 120 + col * 860
        y = 300 + row * 110
        edge = AMBER if name == "ESCALATE" else EMERALD if name == "ALLOW" else CARD_EDGE
        fill = AMBER if name == "ESCALATE" else EMERALD if name == "ALLOW" else MUTED
        round_card(fr, (x, y, x + 780, y + 88), CARD, edge, a, 18)
        blit_text(fr, (x + 28, y + 28), name, F["check"], fill, a)
    blit_text(fr, (120, 720), "GuardRoute makes the call first.", F["name"], TEXT, fade(local, 2.3, 3.0))
    blit_text(fr, (120, 800), "guardroute.ai", F["body"], AMBER, fade(local, 3.1, 3.8))


def draw(t: float) -> Image.Image:
    fr = Frame()
    if t < 5:
        scene_open(fr, t)
    elif t < 12:
        scene_request(fr, t)
    elif t < 18:
        scene_allow(fr, t)
    elif t < 23:
        scene_change(fr, t)
    elif t < 32:
        scene_escalate(fr, t)
    elif t < 39:
        scene_split(fr, t)
    else:
        scene_close(fr, t)
    bar(fr, t)
    return fr.finish()


def main() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "16",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    poster_frame = int(34.5 * FPS)
    for i in range(N):
        frame = draw(i / FPS)
        if i == poster_frame:
            frame.save(POSTER, quality=92)
        proc.stdin.write(frame.tobytes())
        if i % 150 == 0:
            print(f"frame {i}/{N}", flush=True)
    proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise SystemExit(code)
    print(OUT, OUT.stat().st_size)
    print(POSTER, POSTER.stat().st_size)


if __name__ == "__main__":
    main()
