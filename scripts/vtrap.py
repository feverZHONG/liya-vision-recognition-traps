#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vtrap —— 视觉识图工具统一入口（vision-recognition-traps skill）

子命令（后面直接跟各自脚本的原参数）：
  ocr  <图...>       界面/表格文字真 OCR：rapidocr，带坐标框，可裁块放大复核
                     → scripts/ui_ocr.py   选项 --dir --write --json --crop --scale --out --read
  diff <图A> <图B>   两图差分定位（水印/改图取证）：归一化 → 逐像素差分 → 连通域热点表
                     → scripts/imgdiff.py  选项 --grid --top --thresh

例子：
  vtrap ocr shot.png --json /tmp/blocks.json
  vtrap ocr shot.png --crop 495,300,700,420 --scale 6 --read
  vtrap diff 有水印.jpg 无水印.jpg --top 8

解释器：OCR 依赖 rapidocr——优先 $VTRAP_PYTHON；没设就找仓库根的 .venv；都没有则用当前 python。
子命令原脚本照旧可单独跑，本入口只做分发，不改它们的行为。
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUBS = {"ocr": "ui_ocr.py", "diff": "imgdiff.py"}


def pick_python() -> str:
    """OCR 要 rapidocr，优先环境变量，其次仓库 .venv（skills/<name>/scripts/ 上溯）。"""
    env = os.environ.get("VTRAP_PYTHON")
    if env:
        return env
    for i in (2, 1, 3):
        try:
            cand = HERE.parents[i] / ".venv" / "bin" / "python3"
        except IndexError:
            continue
        if cand.exists():
            return str(cand)
    return sys.executable


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print((__doc__ or "").strip())
        return 0
    sub = argv[0]
    if sub not in SUBS:
        print(f"未知子命令: {sub}\n可用: {' / '.join(SUBS)}（-h 看用法）", file=sys.stderr)
        return 2
    script = HERE / SUBS[sub]
    if not script.exists():
        print(f"找不到 {script}", file=sys.stderr)
        return 1
    if sub == "ocr":
        print(f"[vtrap] {Path(pick_python()).name} → {SUBS[sub]}", file=sys.stderr)
    return subprocess.call([pick_python(), str(script)] + argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
