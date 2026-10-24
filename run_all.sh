#!/bin/sh
# Registered runs (Amendment 2). Idempotent: finished episodes are skipped.
P=../../backend/venv/Scripts/python.exe
for m in gpt-6.1-sol gpt-6-luna; do
  ( for w in posctrl posctrl2 posctrl3; do $P run.py --model $m --which $w --workers 8; done
    $P run.py --model $m --which grid --seeds 16 --workers 8 ) > logs_$m.txt 2>&1 &
done
$P run.py --model gpt-5.4-mini --which posctrl --workers 8 > logs_gpt-5.4-mini.txt 2>&1 &
wait
echo ALL DONE
