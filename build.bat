@echo off
if not exist venv (
    echo Virtual environment not found. Please run set up first.
    pause
    exit /b
)
call venv\Scripts\activate
echo Building FlowDown...
pyinstaller --noconsole --onefile --name FlowDown --add-data "web;web" --clean main.py
echo.
echo Build complete! Executable is in dist\FlowDown.exe
pause
