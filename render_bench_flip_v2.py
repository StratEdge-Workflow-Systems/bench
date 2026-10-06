#!/usr/bin/env python3
"""Render bench-flip-v2 silent demo (1280x720, ~8s loop)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

W, H = 1280, 720
FPS = 30
DURATION_S = 8.0
N_FRAMES = int(FPS * DURATION_S)

BG = (2, 8, 23)
MUTED = (100, 116, 139)
TEXT = (226, 232, 240)
ALLOW = (126, 224, 198)
ESCALATE = (240, 193, 77)
CARD_BORDER = (30, 41, 59)
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"

OUT_MP4 = Path(__file__).resolve().parent / "bench-flip-v2.mp4"
OUT_GIF = Path(__file__).resolve().parent / "bench-flip-v2.gif"


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    return {
        "title": ImageFont.truetype(FONT_PATH, 56, index=0),
        "title_sm": ImageFont.truetype(FONT_PATH, 42, index=0),
        "name": ImageFont.truetype(FONT_PATH, 22, index=0),
        "amount": ImageFont.truetype(FONT_PATH, 36, index=0),
        "verdict": ImageFont.truetype(FONT_PATH, 30, index=0),
        "line": ImageFont.truetype(FONT_PATH, 28, index=0),
        "footer": ImageFont.truetype(FONT_PATH, 15, index=0),
    }


def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, ...],
) -> None:
    tw, th = text_size(font, text)
    x, y = xy
    draw.text((x - tw / 2, y - th / 2), text, font=font, fill=fill)


def composite_column(
    img: Image.Image,
    box: tuple[int, int, int, int],
    payee: str,
    amount: str,
    verdict: str,
    verdict_color: tuple[int, ...],
    fonts: dict[str, ImageFont.FreeTypeFont],
    alpha: float,
    tint: tuple[int, int, int],
) -> None:
    if alpha <= 0.01:
        return
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = box
    fill = (*tint, int(42 * alpha))
    border = (*CARD_BORDER, int(230 * alpha))
    od.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=fill, outline=border, width=2)
    cx = (x0 + x1) / 2
    lines = [(payee, fonts["name"], TEXT), (amount, fonts["amount"], TEXT), (verdict, fonts["verdict"], verdict_color)]
    start_y = y0 + 88
    for i, (txt, font, color) in enumerate(lines):
        tw, th = text_size(font, txt)
        fc = (*color[:3], int(255 * alpha))
        od.text((cx - tw / 2, start_y + i * 56), txt, font=font, fill=fc)
    img.alpha_composite(overlay)


def scene_progress(frame: int) -> dict[str, float]:
    """Returns animation weights 0..1 for each layer. Frame 0 == frame N_FRAMES for loop."""
    t = frame / N_FRAMES
    # Phases (fraction of timeline)
    title_center = 1.0
    title_y = 0.35 * H  # center-ish

    # 0.00-0.08: title fade in at center
    # 0.08-0.18: hold title center
    # 0.18-0.38: title moves up, columns in
    # 0.38-0.55: hold columns
    # 0.55-0.65: payee line
    # 0.65-0.75: footer
    # 0.75-0.88: hold full
    # 0.88-1.00: collapse to title-only (match start)

    def seg(start: float, end: float) -> float:
        if t < start:
            return 0.0
        if t > end:
            return 1.0
        return (t - start) / (end - start)

    collapse = ease_in_out_cubic(seg(0.88, 1.0))
    expand = ease_in_out_cubic(seg(0.18, 0.38))
    layout = expand * (1.0 - collapse)

    title_y_target_top = 118
    title_y_center = H * 0.38
    title_y_pos = lerp(title_y_center, title_y_target_top, layout)

    col_master = layout
    col_left = col_master * ease_out_cubic(min(1.0, seg(0.18, 0.32) / 0.14 + 0.001))
    col_right = col_master * ease_out_cubic(min(1.0, max(0.0, seg(0.22, 0.36) / 0.14)))

    line_p = ease_out_cubic(seg(0.52, 0.62)) * (1.0 - collapse)
    footer_p = ease_out_cubic(seg(0.62, 0.72)) * (1.0 - collapse)

    # Seamless loop: title-only beats at t≈0 and t≈1
    title_op = 1.0

    return {
        "title_op": title_op,
        "title_y": title_y_pos,
        "col_left": col_left,
        "col_right": col_right,
        "line": line_p,
        "footer": footer_p,
        "layout": layout,
    }


def render_frame(frame: int, fonts: dict[str, ImageFont.FreeTypeFont]) -> Image.Image:
    p = scene_progress(frame)
    img = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)

    # Subtle top glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W // 2 - 420, -180, W // 2 + 420, 220], fill=(15, 30, 60, 35))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    title_font = fonts["title_sm"] if p["layout"] > 0.3 else fonts["title"]
    title_color = (*TEXT, int(255 * p["title_op"]))
    title_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(title_overlay)
    draw_centered(td, (W / 2, p["title_y"]), "ONE FACT.", title_font, title_color)
    img.alpha_composite(title_overlay)

    left_box = (80, 200, 580, 420)
    right_box = (700, 200, 1200, 420)
    composite_column(
        img,
        left_box,
        "NORTHLINE CUSTODIAL",
        "$4,200",
        "ALLOW",
        ALLOW,
        fonts,
        p["col_left"],
        (12, 50, 45),
    )
    composite_column(
        img,
        right_box,
        "HARBOR RELAY LLC",
        "$4,200",
        "ESCALATE",
        ESCALATE,
        fonts,
        p["col_right"],
        (55, 45, 18),
    )

    if p["layout"] > 0.05:
        div_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(div_overlay)
        mid_a = int(80 * p["layout"])
        dd.line([(640, 230), (640, 390)], fill=(*MUTED, mid_a), width=1)
        img.alpha_composite(div_overlay)

    if p["line"] > 0.01:
        line_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(line_overlay)
        draw_centered(ld, (W / 2, 468), "The payee changed.", fonts["line"], (*TEXT, int(255 * p["line"])))
        img.alpha_composite(line_overlay)

    if p["footer"] > 0.01:
        foot_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(foot_overlay)
        footer_text = (
            "GuardRoute is the live product. Bench is the public rehearsal. Not a customer result."
        )
        tw, th = text_size(fonts["footer"], footer_text)
        fd.text(
            ((W - tw) / 2, H - 56),
            footer_text,
            font=fonts["footer"],
            fill=(*MUTED, int(255 * p["footer"])),
        )
        img.alpha_composite(foot_overlay)

    return img.convert("RGB")


def write_frames(frames_dir: Path) -> None:
    fonts = load_fonts()
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i in range(N_FRAMES):
        render_frame(i, fonts).save(frames_dir / f"frame_{i:04d}.png", optimize=True)


def encode_mp4(frames_dir: Path, out: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pattern = str(frames_dir / "frame_%04d.png")
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def encode_gif(frames_dir: Path, out: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pattern = str(frames_dir / "frame_%04d.png")
    palette = frames_dir / "palette.png"
    cmd_palette = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        pattern,
        "-vf",
        f"fps={FPS},scale=1280:720:flags=lanczos,palettegen=max_colors=128",
        str(palette),
    ]
    subprocess.run(cmd_palette, check=True, capture_output=True)
    cmd_gif = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        pattern,
        "-i",
        str(palette),
        "-lavfi",
        f"fps={FPS},scale=1280:720:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
        "-loop",
        "0",
        str(out),
    ]
    subprocess.run(cmd_gif, check=True, capture_output=True)


def probe_duration(path: Path) -> float:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-i",
        str(path),
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # Duration: HH:MM:SS.ms in stderr
    for line in proc.stderr.splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return DURATION_S


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bench_flip_v2_") as tmp:
        frames_dir = Path(tmp) / "frames"
        print(f"Rendering {N_FRAMES} frames…")
        write_frames(frames_dir)
        print(f"Encoding {OUT_MP4}…")
        encode_mp4(frames_dir, OUT_MP4)
        print(f"Encoding {OUT_GIF}…")
        encode_gif(frames_dir, OUT_GIF)

    mp4_size = OUT_MP4.stat().st_size
    gif_size = OUT_GIF.stat().st_size
    dur = probe_duration(OUT_MP4)
    print(f"MP4: {OUT_MP4} ({mp4_size:,} bytes, {dur:.3f}s)")
    print(f"GIF: {OUT_GIF} ({gif_size:,} bytes)")


if __name__ == "__main__":
    main()
