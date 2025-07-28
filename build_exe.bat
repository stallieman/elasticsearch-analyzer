@echo off
echo =================================================
echo  Flask Index Compare Tool - EXE Builder
echo =================================================
echo.

echo Installeren van PyInstaller...
pip install pyinstaller

echo.
echo Bouwen van executable...
pyinstaller --clean production.spec

echo.
echo =================================================
echo  Build voltooid!
echo =================================================
echo.
echo Het executable bestand is beschikbaar in:
echo   dist\flask_index_compare_tool.exe
echo.
echo Om de applicatie te gebruiken:
echo 1. Kopieer het hele 'dist' folder naar de gewenste locatie
echo 2. Voer flask_index_compare_tool.exe uit
echo 3. De browser opent automatisch op http://127.0.0.1:5000
echo.
pause
