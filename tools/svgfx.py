# -*- coding: utf-8 -*-
r"""MS VIEWER(3편만) 위 띠 그림 한글화(2026-10-10, 하스피 스샷 «形式番号»·«EFREET 改»)
  SV_1.BIN 안 320×24 4비트(LUT 모드) 띠 11장 — 기체마다 «形式番号 + 형식 + 이름», 시작 오프셋 HEADERS(«形式番号» 줄로 찾음)
  색: 14 초록 바탕 · 1 흰 획 · 2‥13 가장자리(덮임 낮을수록 큰 번호, 원본 분포)
  바꿈: «形式番号»(x 8‥58, y 8‥19) → «형식번호» 11장 · EFREET 띠 «改»(x 289‥303) → «개»
  python tools/svgfx.py   → work/gfx/sv_headers_kr.png 미리보기
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import scgfx

W, H = 320, 24
HEADERS = [0x279DC, 0x2899C, 0x2981C, 0x2A7DC, 0x2B65C, 0x2C57C, 0x2D49C, 0x2E3BC, 0x2F2DC, 0x301FC, 0x3111C]
LABEL = (6, 7, 61, 21, '형식번호', 'Galmuri11-Bold.ttf', 12)   # (x0, y0, x1, y1, 글, 글꼴, 크기) — 원본 잉크 x 8‥58, y 8‥19
KAI = (0x2C57C, (287, 5, 306, 21, '개', 'Galmuri14.ttf', 15))   # EFREET 改
BG = 14
GAL = r'C:\claude\utils\font\Galmuri-v2.40.3'   # ★비트맵 글꼴 그대로(하스피 2026-10-11 «형식번호 못생겼어» — 나눔 축소 안티에일리어싱이 뭉개짐)


def ink(px, box):
    """비트맵 글꼴을 안티에일리어싱 없이 찍음(획 = 1 흰색), 칸 가운데"""
    x0, y0, x1, y1, text, fn, size = box
    w, h = x1 - x0, y1 - y0
    F = ImageFont.truetype(os.path.join(GAL, fn), size)
    im = Image.new('1', (w + 20, h + 20), 0); dr = ImageDraw.Draw(im); dr.fontmode = '1'
    dr.text((10, 10), text, font=F, fill=1)
    a = np.array(im); ys, xs = np.where(a)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; gh, gw = a.shape
    assert gw <= w and gh <= h, (text, gw, gh, w, h)
    sub = np.full((h, w), BG, np.uint8)
    oy, ox = (h - gh) // 2, (w - gw) // 2
    sub[oy:oy + gh, ox:ox + gw][a] = 1
    px[y0:y1, x0:x1] = sub
    return px


def patch(sv1):
    d = bytearray(sv1)
    for o in HEADERS:
        px = scgfx.get4(d, o, W, H)
        assert (px[y] for y in range(H)), o
        ink(px, LABEL)
        if o == KAI[0]: ink(px, KAI[1])
        scgfx.put4(d, o, px)
    assert len(d) == len(sv1)
    return bytes(d)


def preview():
    import disc
    o = disc.read('/SV_1.BIN'); n = patch(o)
    rows = []
    for b in HEADERS:
        rows += [scgfx.get4(o, b, W, H), scgfx.get4(n, b, W, H), np.full((3, W), 15, np.uint8)]
    img = np.vstack(rows)
    pal = np.array([(0, 0, 0)] + [(255 - 12 * i,) * 3 for i in range(1, 14)] + [(16, 112, 16), (0, 0, 0)], np.uint8)
    Image.fromarray(pal[img]).resize((W * 3, img.shape[0] * 3), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', 'sv_headers_kr.png'))
    diff = [i for i in range(len(o)) if o[i] != n[i]]
    rng = [(b, b + W * H // 2) for b in HEADERS]
    print('바뀐', len(diff), '띠 밖', sum(1 for i in diff if not any(a <= i < c for a, c in rng)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    preview()
