@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 活动代币计算器 - 数据更新

set PYTHONIOENCODING=utf-8
set "SCRIPT=%~dp0更新活动数据.py"

rem 1) 开发机自带的运行时，别处没有，找不到就算了
if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" "%SCRIPT%"
  goto done
)

rem 2) Python 启动器
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 (
  py -3 "%SCRIPT%"
  goto done
)

rem 3) PATH 里的 python，逐个试，跳过应用商店的空壳
for /f "delims=" %%P in ('where python 2^>nul') do (
  "%%P" -c "import sys" >nul 2>nul
  if not errorlevel 1 (
    "%%P" "%SCRIPT%"
    goto done
  )
)

rem 4) 常见安装目录，PATH 没配也能找到
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
  if exist "%%D\python.exe" (
    "%%D\python.exe" "%SCRIPT%"
    goto done
  )
)
for /d %%D in ("C:\Python3*") do (
  if exist "%%D\python.exe" (
    "%%D\python.exe" "%SCRIPT%"
    goto done
  )
)

echo.
echo   没有找到能用的 Python。
echo.
echo   这个功能要装 Python 才能用，装的时候记得勾上
echo   「Add Python to PATH」，不然系统找不到它。
echo.
echo   下载地址：https://www.python.org/downloads/
echo.
echo   只是想看数据、不打算自己更新的话，直接双击 index.html，
echo   不装任何东西也能用。
echo.

:done
echo.
pause
