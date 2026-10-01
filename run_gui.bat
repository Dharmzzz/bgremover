@echo off
title Image Background Remover
cd /d "%~dp0"
echo Launching Image Background Remover GUI...
start "" pythonw bg_remover.py --gui
exit
