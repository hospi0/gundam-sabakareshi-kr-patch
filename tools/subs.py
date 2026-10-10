# -*- coding: utf-8 -*-
r"""건담 외전 III 음성 자막 자료(2026-10-10, 1편 tools/subs.py 에서 — 글꼴 한 벌 공유·표 NT 칸) — 번역 줄 → 쪽 → 덩어리별 묶음(다이노 poc2.payload 꼴) → 상주 블롭 표.
  묶음:  +0 'DSUB' · +4 u16 쪽 수 · +6 u16 0 · +12 u16 글꼴 자리 · +16 쪽 표[쪽 수](u16 t0, u16 t1, u16 쪽 자리, u16 0)
         쪽 = glyphpack 꼴(u8 w8, u8 nrow, u8 c0, u8 글자 수, 글자마다 3 B) · 글꼴 = 글자마다 18 B(12×12 1비트)
         t = 1/60초, 덩어리 처음부터(머리 없음).
  블롭 표: 스트림 번호(SS_SND 표 번호 − 6 = 스트림 구조 +4 값) 0‥NT−1 → 묶음 주소(없으면 0). 글꼴은 모든 묶음 뒤 한 벌.
  쪽 글자 3 B: 번호 아래 8비트 · x 아래 8비트 · (x>>8) | 줄<<1 | (번호>>8)<<2  (번호 < 16384)
"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.append(r'C:\claude\project\burningrangers-kr-patch\tools')
import glyphpack as G

G.MAXW = 300
MINP = 0.8; LINGER = 0.3
PUNCT_SP = re.compile(r'([,.!?:;)\]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥]) +')

def clean(t):
    return PUNCT_SP.sub(r'\1', t.strip())


def check_glyphs(t, where):
    for c in t:
        if c == ' ': continue
        if not any(G.glyph(c)): raise SystemExit('글꼴에 없는 글자 %r — %s' % (c, where))


def pages_for(rows):
    """[(초, 초, 번역)] → [(t0초, t1초, [줄…])] — 다이노 build.pages_for 와 같음"""
    rows = sorted(rows); out = []
    for i, (s, e, ko) in enumerate(rows):
        ko = clean(ko); check_glyphs(ko, ko)
        nxt = rows[i + 1][0] if i + 1 < len(rows) else None
        pg = G.pages_of(ko)
        lens = [max(1, len(''.join(p).replace(' ', ''))) for p in pg]; tot = sum(lens); acc = 0
        end = max(e + LINGER, s + MINP * len(pg))
        if nxt is not None: end = min(end, max(nxt, s + MINP * len(pg)))
        for p, L in zip(pg, lens):
            t0 = s + (end - s) * acc / tot; acc += L
            out.append([t0, s + (end - s) * acc / tot, p])
    for a, b in zip(out, out[1:]):
        if a[1] > b[0]: a[1] = b[0]
    return [(a, b, p) for a, b, p in out]


def payload(rows, gi):
    """→ (묶음(글꼴 자리 칸 = 0, blob 이 채움), 쪽들) — gi = 전체 글꼴 번호(한 벌 공유, 2·3편)"""
    pages = [(int(round(a * 60)), int(round(b * 60)), p) for a, b, p in pages_for(rows)]
    lay = [G.layout(l) for _, _, l in pages]
    recs = []
    for w8, nrow, chars in lay:
        assert w8 * nrow <= 255 and w8 <= 40
        r = bytes([w8, nrow, (40 - w8) // 2, len(chars)])
        for c, x, ln in chars:
            assert gi[c] < 1 << 14 and x < 512
            r += bytes([gi[c] & 0xFF, x & 0xFF, (x >> 8) | ln << 1 | (gi[c] >> 8) << 2])
        recs.append(r + bytes(-len(r) % 4))
    offs = []; o = 16 + 8 * len(pages)
    for r in recs: offs.append(o); o += len(r)
    tab = b''.join(struct.pack('>HHHH', t0, t1, offs[i], 0) for i, (t0, t1, _) in enumerate(pages))
    b = b'DSUB' + struct.pack('>HH', len(pages), 0) + bytes(8) + tab + b''.join(recs)
    return b + bytes(-len(b) % 4), pages


TSV = os.path.join(ROOT, 'work', 'text', 'voice_ko.tsv')


def load():
    """work/text/voice_ko.tsv(id·시작·끝·원문·번역) → {'V25': [(초, 초, 번역)…]} — 번역 빈 줄은 자막 없음"""
    out = {}
    for ln in open(TSV, encoding='utf-8').read().splitlines()[1:]:
        c = ln.split('	')
        if len(c) < 5 or not c[4].strip(): continue
        out.setdefault(c[0].split('_')[0], []).append((float(c[1]), float(c[2]), c[4].strip()))
    return out


def blob(base, voices=None):
    """상주 자료: 표 NT×u32(스트림 번호 → 묶음 주소) + 묶음 머리들 + 쪽 기록 모음(같은 쪽은 한 번만) + 글꼴 한 벌
       묶음 +12 = 글꼴까지 거리(u16) · 쪽 표의 쪽 자리 = 묶음 머리에서 쪽 기록까지 거리(u16, 앞으로만)
       ★2편: V12/13·V56/57·V58/59 가 계급만 다른 같은 대사 → 쪽 기록 공유로 자리 절약(S0_1 뒤 18 KB)"""
    import hook
    voices = voices or load()
    gl = []; gi = {}
    for v, rows in sorted(voices.items()):
        for _, _, p in pages_for(rows):
            for c, _, _ in G.layout(p)[2]:
                if c not in gi: gi[c] = len(gl); gl.append(c)
    heads = []; pool = bytearray(); pidx = {}; info = {}
    for v, rows in sorted(voices.items()):
        k = int(v[1:]) - 6
        assert 0 <= k < hook.NT, v
        pages = [(int(round(a * 60)), int(round(b * 60)), p) for a, b, p in pages_for(rows)]
        ents = []
        for t0, t1, lines in pages:
            w8, nrow, chars = G.layout(lines)
            assert w8 * nrow <= 255 and w8 <= 40
            r = bytes([w8, nrow, (40 - w8) // 2, len(chars)])
            for c, x, ln in chars:
                assert gi[c] < 1 << 14 and x < 512
                r += bytes([gi[c] & 0xFF, x & 0xFF, (x >> 8) | ln << 1 | (gi[c] >> 8) << 2])
            r += bytes(-len(r) % 4)
            if r not in pidx: pidx[r] = len(pool); pool += r
            ents.append((t0, t1, pidx[r]))
        heads.append((k, ents)); info[v] = len(pages)
    tabsz = 4 * hook.NT
    hsz = sum(16 + 8 * len(e) for _, e in heads)
    tab = [0] * hook.NT; hb = bytearray(); pool_at = tabsz + hsz; font_at = pool_at + len(pool)
    for k, ents in heads:
        at = tabsz + len(hb); tab[k] = base + at
        assert font_at - at < 0x10000 and pool_at + len(pool) - at < 0x10000
        hb += b'DSUB' + struct.pack('>HH', len(ents), 0) + bytes(4) + struct.pack('>H', font_at - at) + bytes(2)
        hb += b''.join(struct.pack('>HHHH', t0, t1, pool_at + o - at, 0) for t0, t1, o in ents)
    assert len(hb) == hsz
    out = struct.pack('>%dI' % hook.NT, *tab) + bytes(hb) + bytes(pool) + b''.join(G.gbytes(c) for c in gl)
    info['쪽 기록'] = len(pool); info['글꼴'] = (len(gl), 18 * len(gl))
    return out + bytes(-len(out) % 4), info
