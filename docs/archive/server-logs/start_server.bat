@echo off
chcp 65001 >nul
title Qwen2.5-Coder-1.5B (CUDA)
cd /d "%~dp0llama.cpp\cuda"

rem ===== 可改配置 =====
set MODEL=%~dp0models\qwen2.5-coder-1.5b-instruct-q6_k.gguf
rem set MODEL=%~dp0models\qwen2.5-coder-1.5b-instruct-q8_0.gguf
set CTX=8192
set PORT=8080
rem ====================

echo 启动中: %MODEL%
echo 上下文 %CTX% tokens | 端口 http://127.0.0.1:%PORT%
echo OpenAI 兼容接口: http://127.0.0.1:%PORT%/v1/chat/completions
echo 关闭本窗口即停止服务。
echo.
llama-server.exe -m "%MODEL%" -ngl 99 -c %CTX% --parallel 1 --host 127.0.0.1 --port %PORT%
pause
