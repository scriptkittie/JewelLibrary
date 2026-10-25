@echo off
call "%~dp0platform\windows\fetch-covers.bat"
exit /b %errorlevel%
