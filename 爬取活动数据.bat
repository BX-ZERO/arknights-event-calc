@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set "PY="
if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" set "PY=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not defined PY (
  py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo   没找到 Python。
  echo   去 https://www.python.org/downloads/ 装一个，
  echo   安装时勾上「Add Python to PATH」，然后重开这个窗口。
  echo.
  pause
  exit /b 1
)
%PY% "工具\打包全部活动.py"
echo.
pause
