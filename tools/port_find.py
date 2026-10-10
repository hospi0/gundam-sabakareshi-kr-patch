# -*- coding: utf-8 -*-
r"""1편(gundam-blue-kr-patch) 훅 주소를 이 편의 실행 파일에서 찾기(2026-10-10) — 같은 엔진이라 코드 조각이 같다.
  ① S0_0 함수(VBlank-OUT·IN·DMA 끝): 1편 함수 머리 N 바이트를 이 편 S0_0 에서 찾음 → 새 주소 → 그 값을 담은 리터럴 위치
  ② END 견본 리터럴(0x86xxxxxx → S0_0 안 0x8000): 1편 리터럴 앞뒤 코드로 찾음
  ③ 스트림 구조(1.BIN 리터럴 0x06014220): 1편 1.BIN 에서 그 리터럴 근처 코드 → 이 편 1.BIN 의 같은 자리 리터럴 값
  ④ 적재 주소 리터럴(0x00200000·0x00250000·0x06060000)
  python tools/port_find.py
"""
import os, struct, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ONE = r'C:\claude\project\gundam-blue-kr-patch\work\disc'
sys.stdout.reconfigure(encoding='utf-8')


def rd(base, n):
    return open(os.path.join(base, n), 'rb').read()


def find_func(a, b, base, addr, n=32):
    o = addr - base; pat = a[o:o + n]
    hits = []; i = b.find(pat)
    while i >= 0:
        hits.append(base + i); i = b.find(pat, i + 1)
    return hits


def lits(b, base, val):
    v = struct.pack('>I', val); out = []; i = b.find(v)
    while i >= 0:
        if i % 4 == 0: out.append(base + i)
        i = b.find(v, i + 1)
    return out


def main():
    me = os.path.join(ROOT, 'work', 'disc')
    a0, b0 = rd(ONE, 'S0_0.BIN'), rd(me, 'S0_0.BIN')
    B = 0x06020000
    res = {}
    for nm, fn, lit in (('VBI', 0x060449D6, 0x06044BE8), ('VIN', 0x0604487E, 0x06044BE4), ('DMAE', 0x0604486C, 0x06044BF4)):
        for n in (32, 16, 12):
            h = find_func(a0, b0, B, fn, n)
            if len(h) == 1: break
        print(nm, '1편 %X → 이 편' % fn, [hex(x) for x in h], '(머리 %d B)' % n)
        if len(h) == 1:
            L = lits(b0, B, h[0])
            print('   리터럴', [hex(x) for x in L], ' (1편 리터럴 %X, 차이 %X)' % (lit, lit - fn))
            res[nm] = (h[0], L)
    # END 견본: 1편 리터럴 0x06048474 = 0x8604845A
    o = 0x06048474 - B
    for n in (16, 12, 8):
        ctx = a0[o - n:o]
        i = b0.find(ctx)
        if i >= 0 and b0.find(ctx, i + 1) < 0:
            v = struct.unpack_from('>I', b0, i + n)[0]
            t = (v & 0x7FFFFFFF) | 0x06000000
            print('견본 리터럴 %X = %08X → %X 의 값 %04X' % (B + i + n, v, t, struct.unpack_from('>H', b0, t - B)[0] if 0 <= t - B < len(b0) else -1))
            break
    else:
        print('견본 리터럴 못 찾음 — 0x86xxxxxx 후보', [(hex(B + k), hex(struct.unpack_from('>I', b0, k)[0])) for k in range(0, len(b0), 4)
                                                    if struct.unpack_from('>I', b0, k)[0] >> 24 == 0x86][:20])
    # 스트림 구조
    a1, b1 = rd(ONE, '1.BIN'), rd(me, '1.BIN')
    B1 = 0x06003000
    vals = Counter()
    for L in lits(a1, B1, 0x06014220):
        o = L - B1
        for n in (12, 8):
            ctx = a1[o - n:o]; i = b1.find(ctx)
            if i >= 0 and b1.find(ctx, i + 1) < 0:
                vals[struct.unpack_from('>I', b1, i + n)[0]] += 1; break
    print('스트림 구조 후보(1편 0x06014220 자리)', [(hex(k), c) for k, c in vals.most_common(5)], '· 1편 리터럴', len(lits(a1, B1, 0x06014220)))
    for v in (0x00200000, 0x00250000, 0x06060000, 0x06020000):
        print('적재 %08X 리터럴: 1.BIN %d · S0_0 %d' % (v, len(lits(b1, B1, v)), len(lits(b0, B, v))))
    print('S0_0 %d B(1편 %d) · S0_1 %d B · 1.BIN %d B' % (len(b0), len(a0), len(rd(me, 'S0_1.BIN')), len(b1)))
    print('Sn_1 최대', max((len(rd(me, f)), f) for f in os.listdir(me) if f.endswith('_1.BIN') and f != 'S0_1.BIN'))
    # 견본 자리(1편 0x0603BC00): 이 편 S0_0 에서 0 이 0x400 이상 이어진 구간
    runs = []; k = 0
    while k < len(b0):
        if b0[k] == 0:
            j = k
            while j < len(b0) and b0[j] == 0: j += 1
            if j - k >= 0x400: runs.append((hex(B + k), j - k))
            k = j
        else: k += 1
    print('S0_0 0 구간(≥1 KB)', runs[:10])


if __name__ == '__main__':
    main()
