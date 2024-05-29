@echo off
python main.py %*
:restart
if exist .restart (
    python main.py %*
    timeout /t 5
    goto restart
)
