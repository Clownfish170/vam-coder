' Universal windowless resume wrapper: run resume_v13e.bat hidden (window style 0).
' Trigger: Startup folder copy at logon; DS batch no-ops when complete, then Qwen resumes.
' wscript.exe is a GUI host -> no console window at any point.
Option Explicit
Dim sh
Set sh = CreateObject("WScript.Shell")
sh.Run """D:\Demo\DynaMem\vam-coder\p1\experiments\v13e_crossmodel\resume_v13e.bat""", 0, False
Set sh = Nothing
