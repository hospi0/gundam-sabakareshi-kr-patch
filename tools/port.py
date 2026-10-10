# -*- coding: utf-8 -*-
r"""건담 외전 III 훅 주소(2026-10-10, tools/port_find.py 로 1편 주소에서 옮김 — 함수 머리 32 B 일치·리터럴 하나뿐)
  1편(gundam-blue) VBI 0x060449D6/리터럴 0x06044BE8 · VIN 0x0604487E/0x06044BE4 · DMA 끝 0x0604486C/0x06044BF4 · 견본 리터럴 0x06048474 · 스트림 0x06014220
  TPL = 1편 견본(0x3C1 B 0 구간 안 +0x271)과 같은 자리 · RES‥END = S0_1 끝(0x205B44)‥가장 이른 Sn_1 적재
  NT = 스트림 표 칸 수(SS_SND 6번부터)
"""
VBI = 0x6047FA6
VBI_LIT = 0x60481B8
VIN = 0x6047E4E
VIN_LIT = 0x60481B4
DMAE = 0x6047E3C
DMAE_LIT = 0x60481C4
TPL = 0x603F1D0
TPL_LIT = 0x604BA78
TPL_OLD = 0x8604BA5E
STREAM = 0x6014240
RES = 0x205C00
END = 0x210000
NT = 72
S01END = 0x205B44
