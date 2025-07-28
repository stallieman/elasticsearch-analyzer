@echo off
echo ==========================================
echo   Flask Index Compare Tool - Deployment
echo ==========================================
echo.
echo Creating deployment package...
echo.

REM Create deployment folder
if not exist "deployment" mkdir deployment

REM Copy executable and support files
copy flask_index_compare_tool.exe deployment\
copy start_app.bat deployment\
copy GEBRUIKERS_HANDLEIDING.md deployment\

REM Create empty clusters.json if it doesn't exist
if not exist "deployment\clusters.json" echo {} > deployment\clusters.json

echo.
echo ==========================================
echo   Deployment package created!
echo ==========================================
echo.
echo Files in 'deployment' folder:
dir deployment
echo.
echo Ready for distribution to Windows VMs!
echo.
pause
