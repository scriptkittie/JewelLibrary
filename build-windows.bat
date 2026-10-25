@echo off
call "%~dp0platform\windows\build.bat"
exit /b %errorlevel%
