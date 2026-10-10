# -*- coding: utf-8 -*-
r"""고유명사 힌트로 다시 받아쓰기(2026-10-10) → work/asr2/V*.json (asr_all 과 같은 꼴)
  C:\claude\utils\whisper-venv\Scripts\python.exe tools/asr_prompt.py
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import snd
from asr_all import pcm

OUT = os.path.join(ROOT, 'work', 'asr2')
PROMPT = ('機動戦士ガンダム外伝。ユウ・カジマ少尉、フィリップ・ヒューズ少尉、サマナ・フュリス准尉、モーリン・キタムラ伍長。'
          'ジム、ザク、グフ、ドム、ミデア、ジオン、連邦軍、モビルスーツ、ミノフスキー粒子、EXAMシステム、青い死神、ブルーディスティニー。')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(OUT, exist_ok=True)
    from faster_whisper import WhisperModel
    m = WhisperModel('large-v3', device='cuda', compute_type='float16')
    d = open(snd.PATH, 'rb').read(); tb = snd.table(d)
    for k in snd.VOICES:
        base = 'V%02d' % k; p = os.path.join(OUT, base + '.json')
        if os.path.exists(p): continue
        o, s = tb[k]; a, sec = pcm(d[o:o + s])
        seg, _ = m.transcribe(a, language='ja', beam_size=5, word_timestamps=True, initial_prompt=PROMPT,
                              condition_on_previous_text=False, vad_filter=True,
                              vad_parameters={'min_silence_duration_ms': 300})
        segs = [{'s': round(x.start, 2), 'e': round(x.end, 2), 't': x.text.strip(),
                 'w': [[round(w.start, 2), round(w.end, 2), w.word] for w in (x.words or [])]} for x in seg]
        json.dump({'name': base, 'off': o, 'sec': round(sec, 2), 'segs': segs}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        print(base, len(segs), flush=True)


if __name__ == '__main__':
    main()
