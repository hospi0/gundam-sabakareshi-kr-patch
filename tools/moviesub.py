# -*- coding: utf-8 -*-
r"""건담 외전 I 동영상 자막 굽기 (2026-10-10, 버닝 레인저 tools/moviesub.py 에서 — FILM 1.08 · cinepak 160×120 띠 1개 · 30fps · 소리 PCM 조각은 그대로)
  대상: MV_OPD(오프닝 내레이션) · MV_PRV(다음 회 예고 — 화면 글자 «次回予告»·«次回 蒼を受け継ぐ者»도 아래 자막으로, 하스피 «화면 하단에 띄워»)
  자막 표: work/movie/movie_subs.tsv — 영상 · 시작 · 끝(초) · 원문 · 번역(«\n» = 강제 줄바꿈) · 비고
  시간: 읽을 시간(글자×0.15초 + 0.8초, 최소 1.2초)보다 짧으면 다음 자막 앞까지 늘림.
  글씨: 갈무리11 좁은꼴(한글 8px 폭·12px, 비트맵 그대로) 흰색 + 검은 1px 테두리, 화면 아래 가운데(줄 간격 13px), 부호 뒤 공백 1칸 삭제.
  굽기: 자막 든 프레임만 cinepak 재굽기(tools/movenc.py, 프레임마다 원래 크기 이하) → work/kr/<영상>.BIN (원본 크기, 0 채움 — 디스크 제자리)
  미리보기: work/movie/sub/<영상>_kr.mp4
  python tools/moviesub.py [영상 …] [--nopreview]   (없으면 표의 영상 전부)
"""
import glob, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import filmcpk, movenc

FFBIN = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin'
FONT = r'C:\claude\utils\font\Galmuri-v2.40.3\Galmuri11-Condensed.ttf'
PX, W, H = 12, 160, 120
LH = 13
MAXW = W - 6
TSV = os.path.join(ROOT, 'work', 'movie', 'movie_subs.tsv')
SRC = os.path.join(ROOT, 'work', 'disc')
WORK = os.path.join(ROOT, 'work', 'movie')
PUNCT_SP = re.compile(r'([,.!?:;)\]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥]) (?! )')
KANA = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')


def rows():
    out = {}
    for ln in open(TSV, encoding='utf-8').read().splitlines():
        if ln.startswith('#') or ln.startswith('movie\t') or not ln.strip():
            continue
        c = ln.split('\t')
        t = c[4]
        assert t and not KANA.search(t), ('번역 비었거나 가나·한자 남음', c)
        lines = [PUNCT_SP.sub(r'\1', p.strip()) for p in t.split('\\n')]
        out.setdefault(c[0], []).append((float(c[1]), float(c[2]), lines))
    return out


def need(lines):
    return max(sum(len(p) for p in lines) * 0.15 + 0.8, 1.2)


def events(rs, dur):
    ev = []
    for k, (s, e, lines) in enumerate(rs):
        nxt = rs[k + 1][0] if k + 1 < len(rs) else dur
        end = min(max(e, s + need(lines)), nxt - 0.07, dur - 0.05)
        ev.append((s, end, lines))
    return ev


def plate(lines, F):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.fontmode = '1'                                        # 비트맵 글꼴 — 번짐 없이
    for ln in lines:
        assert d.textlength(ln, font=F) <= MAXW, ('줄 넘침', ln)
    assert len(lines) <= 2, ('세 줄 이상', lines)
    y = H - 9 - (len(lines) - 1) * LH
    for ln in lines:
        x = (W - int(d.textlength(ln, font=F))) // 2
        d.text((x, y), ln, font=F, anchor='ls', fill=(255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0)); y += LH
    px = im.load()
    for yy in range(H):
        for xx in range(W):
            r, g, b, a = px[xx, yy]
            px[xx, yy] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
    return im


def frames(name):
    fr = os.path.join(WORK, 'frames', name.lower())
    if not glob.glob(os.path.join(fr, 'f*.png')):
        os.makedirs(fr, exist_ok=True)
        subprocess.run([os.path.join(FFBIN, 'ffmpeg.exe'), '-v', 'error', '-y', '-i', os.path.join(SRC, name + '.BIN'),
                        '-fps_mode', 'passthrough', os.path.join(fr, 'f%04d.png')], check=True)
    return fr


def times(name):
    """영상 프레임마다 (시작, 끝) 초 — STAB 정보1(기준 film['base'] 틱)"""
    film = filmcpk.read(open(os.path.join(SRC, name + '.BIN'), 'rb').read())
    v = [e for e in film['stab'] if e[2] != 0xFFFFFFFF]
    return [((e[2] & 0x7FFFFFFF) / film['base'], ((e[2] & 0x7FFFFFFF) + e[3]) / film['base']) for e in v]


def burn(name, ev, log):
    fr = frames(name)
    T = times(name)
    nf = len(glob.glob(os.path.join(fr, 'f*.png')))
    assert nf == len(T), ('프레임 수 불일치', nf, len(T))
    kr = os.path.join(fr, 'kr'); os.makedirs(kr, exist_ok=True)
    for f in glob.glob(os.path.join(kr, 'f*.png')):
        os.remove(f)
    F = ImageFont.truetype(FONT, PX); done = 0
    for a, b, lines in ev:
        pl = plate(lines, F)
        for f, (t0, t1) in enumerate(T):
            if t0 < b and t1 > a and (min(t1, b) - max(t0, a)) >= 0.5 * (t1 - t0):
                p = os.path.join(kr, 'f%04d.png' % (f + 1))
                im = Image.open(p if os.path.exists(p) else os.path.join(fr, 'f%04d.png' % (f + 1))).convert('RGBA')
                im.alpha_composite(pl)
                im.convert('RGB').save(p); done += 1
    src = os.path.join(SRC, name + '.BIN')
    dst = os.path.join(ROOT, 'work', 'kr', name + '.BIN')
    size = os.path.getsize(src)
    movenc.reencode(src, fr, kr, dst, size, log=log)
    d = open(dst, 'rb').read()
    open(dst, 'wb').write(d + bytes(size - len(d)))
    log('%s 프레임 %d/%d 에 자막 → %s' % (name, done, nf, dst))


def preview(name):
    os.makedirs(os.path.join(WORK, 'sub'), exist_ok=True)
    subprocess.run([os.path.join(FFBIN, 'ffmpeg.exe'), '-v', 'error', '-y', '-i', os.path.join(ROOT, 'work', 'kr', name + '.BIN'),
                    '-vf', 'scale=%d:%d:flags=neighbor' % (W * 4, H * 4), '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', os.path.join(WORK, 'sub', name + '_kr.mp4')], check=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    allr = rows()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = args or sorted(allr)
    log = lambda *a: print(*a, flush=True)
    F = ImageFont.truetype(FONT, PX)
    for name in sorted(allr):                                   # 먼저 전부 폭 검사
        for _, _, lines in allr[name]:
            plate(lines, F)
    for name in names:
        T = times(name)
        ev = events(allr[name], T[-1][1])
        log('== %s 자막 %d개' % (name, len(ev)))
        for a, b, t in ev:
            log('   %6.2f‥%6.2f  %s' % (a, b, ' / '.join(t)))
        burn(name, ev, log)
        if '--nopreview' not in sys.argv:
            preview(name)


if __name__ == '__main__':
    main()
