# -*- coding: utf-8 -*-
r"""동영상(MV_OPD·MV_PRV) 받아쓰기(위스퍼 large-v3, 구간 시각) → work/movie/asr/<이름>.tsv (시작·끝·문장)
   C:\claude\utils\whisper-venv\Scripts\python.exe tools/asr_movie.py [이름 …]"""
import os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe'
m = WhisperModel('large-v3', device='cuda', compute_type='float16')
for n in sys.argv[1:] or ['MV_OPD', 'MV_PRV']:
    p = os.path.join(ROOT, 'work', 'disc', n + '.BIN')
    raw = subprocess.run([FF, '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    seg, _ = m.transcribe(a, language='ja', beam_size=5, condition_on_previous_text=False, word_timestamps=True,
                          initial_prompt='ユウ・カジマ、モーリン・キタムラ、ジオン、ザク、ジム、連邦、ニムバス、イフリート、ブルーディスティニー')
    with open(os.path.join(ROOT, 'work', 'movie', 'asr', n + '.tsv'), 'w', encoding='utf-8') as fo:
        for s in seg:
            fo.write('%.2f\t%.2f\t%s\n' % (s.start, s.end, s.text.strip()))
            print(n, '%.2f\t%.2f\t%s' % (s.start, s.end, s.text.strip()), flush=True)
