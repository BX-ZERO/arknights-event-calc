@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 活动代币计算器

set PYTHONIOENCODING=utf-8
set "SCRIPT=%~dp0本地服务.py"

rem 本机自带的运行时（仅开发机有）
if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" "%SCRIPT%"
  goto done
)

rem 有些电脑 PATH 里的 python 是应用商店的空壳，先试能不能真的执行
py -3 -c "import sys" >nul 2>nul
if %errorlevel%==0 (
  py -3 "%SCRIPT%"
  goto done
)

python -c "import sys" >nul 2>nul
if %errorlevel%==0 (
  python "%SCRIPT%"
  goto done
)

echo.
echo   没有找到能用的 Python。
echo.
echo   这个功能要装 Python 才能用，装的时候记得勾上
echo   「Add Python to PATH」，不然系统找不到它。
echo.
echo   下载地址：https://www.python.org/downloads/
echo.
echo   只是想看数据、不打算自己更新的话，直接双击 index.html 就行，
echo   不装任何东西也能用。
echo.

:done
echo.
pause
