# -*- coding: utf-8 -*-
r"""SS_SND.BIN 읽기(2026-10-10)
  머리 0x800: u32 BE [0]=0x800, [1..6]=그룹 표 위치, 0x1C 부터 (오프셋, 크기) 쌍 30개.
  6‥29번 = 음성 스트림 — 16비트 BE PCM ★스테레오(좌우 번갈아) 22,050 Hz = 88,200 B/초, 머리 없음. 0‥5 = 소리 은행.
  ★2026-10-10 처음엔 모노로 잘못 읽음(받아쓰기 엉망, V06 은 소리부터 엉망) — 24개 모두 스테레오가 인식 신뢰도 높음(work/stereo_probe.py).
"""
import os, struct
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'work', 'disc', 'SS_SND.BIN')
RATE = 22050; CH = 2; BPS = RATE * 2 * CH       # 초당 바이트
VOICES = range(6, 75)


def table(d=None):
    d = d or open(PATH, 'rb').read()
    w = struct.unpack_from('>512I', d, 0); out = []; i = 0x1C // 4
    while i + 1 < 512 and w[i]:
        out.append((w[i], w[i + 1])); i += 2
    return out


def voice(k, d=None):
    d = d or open(PATH, 'rb').read(); o, s = table(d)[k]
    return d[o:o + s]


def mono(b):
    """스테레오 16비트 BE → 좌우 평균 float32(−1‥1)"""
    import numpy as np
    a = np.frombuffer(b[:len(b) // 4 * 4], '>i2').astype(np.float32) / 32768
    return (a[0::2] + a[1::2]) / 2
