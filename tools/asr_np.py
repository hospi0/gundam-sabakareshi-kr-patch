# -*- coding: utf-8 -*-
r"""음성 스트림 전부 받아쓰기(2026-10-10, 다이노 asr_all 꼴) — 위스퍼 large-v3, 낱말 시각까지.
  SS_SND 6‥29번 = 16비트 BE PCM 스테레오 22,050 Hz → 좌우 평균 → 16 kHz numpy 로 넘김.
  → work/asr/V<번호>.json  {"name", "off", "sec", "segs": [{"s","e","t","w": [[s,e,낱말]…]}]}  (이미 있으면 건너뜀)
  C:\claude\utils\whisper-venv\Scripts\python.exe tools/asr_all.py
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import snd

OUT = os.path.join(ROOT, 'work', 'asr_np')                       # 스테레오(1편에서 확인) · 고유명사 힌트
PROMPT = '機動戦士ガンダム外伝。ユウ・カジマ少尉、フィリップ・ヒューズ少尉、サマナ・フュリス准尉、モーリン・キタムラ伍長、ニムバス・シュターゼン、ブルーディスティニー1号機・2号機・3号機、EXAMシステム、ジム、ザク、グフ、ドム、イフリート改、ジオン、連邦軍、モビルスーツ、ミノフスキー粒子、蒼い死神。'


def pcm(b):
    a = snd.mono(b)                                                   # ★스테레오(2026-10-10)
    idx = np.arange(0, len(a), snd.RATE / 16000)
    return np.interp(idx, np.arange(len(a)), a).astype(np.float32), len(a) / snd.RATE


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(OUT, exist_ok=True)
    from faster_whisper import WhisperModel
    m = WhisperModel('large-v3', device='cuda', compute_type='float16')
    d = open(snd.PATH, 'rb').read(); tb = snd.table(d)
    for k in snd.VOICES:
        base = 'V%02d' % k; p = os.path.join(OUT, base + '.json')
        if os.path.exists(p):
            continue
        o, s = tb[k]; a, sec = pcm(d[o:o + s])
        seg, _ = m.transcribe(a, language='ja', beam_size=5, word_timestamps=True, initial_prompt=None,
                              condition_on_previous_text=False, vad_filter=True,
                              vad_parameters={'min_silence_duration_ms': 300})
        segs = [{'s': round(x.start, 2), 'e': round(x.end, 2), 't': x.text.strip(),
                 'w': [[round(w.start, 2), round(w.end, 2), w.word] for w in (x.words or [])]} for x in seg]
        json.dump({'name': base, 'off': o, 'sec': round(sec, 2), 'segs': segs}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        print('%s %.1f초 %d조각 | %s' % (base, sec, len(segs), ' / '.join(x['t'] for x in segs)[:80]), flush=True)


if __name__ == '__main__':
    main()
