@echo off
chcp 65001 >nul
title Qwen2.5-Coder-1.5B 聊天
cd /d "%~dp0llama.cpp\cuda"
set MODEL=%~dp0models\qwen2.5-coder-1.5b-instruct-q6_k.gguf
echo 交互聊天中 (CUDA). 输入 /exit 退出。
llama-cli.exe -m "%MODEL%" -ngl 99 -c 4096 --no-warmup
pause
