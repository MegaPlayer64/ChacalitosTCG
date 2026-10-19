@echo off
:: ============================================================
::  ChacalitosTCG - Script de Instalacion de Dependencias
::  Compatible con: Windows 10/11
:: ============================================================

title ChacalitosTCG - Instalador de Dependencias
color 0B

echo.
echo  ============================================
echo   ChacalitosTCG - Instalador de Dependencias
echo  ============================================
echo.

:: ---- Verificar Python ----
echo [*] Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [X] ERROR: Python no esta instalado.
    echo     Descargalo desde https://python.org ^(marca "Add to PATH"^)
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i encontrado.

:: ---- Verificar pip ----
echo [*] Verificando pip...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [X] ERROR: pip no esta disponible.
    pause
    exit /b 1
)
echo [OK] pip disponible.

:: ---- Actualizar pip ----
echo [*] Actualizando pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip actualizado.

:: ---- Instalar dependencias Python ----
echo.
echo [*] Instalando dependencias Python del proyecto...
echo.

set FAILED=0

call :install_dep "kivy[base]"         "Kivy              (motor de UI principal)"
call :install_dep "psutil"             "psutil            (monitoreo del sistema)"
call :install_dep "requests"           "requests          (peticiones HTTP / cloud sync)"
call :install_dep "PyJWT"              "PyJWT             (tokens de autenticacion)"
call :install_dep "fastapi"            "FastAPI           (servidor REST)"
call :install_dep "uvicorn[standard]"  "uvicorn           (servidor ASGI para FastAPI)"
call :install_dep "pydantic"           "pydantic          (validacion de datos)"
call :install_dep "passlib[bcrypt]"    "passlib[bcrypt]   (hashing de contrasenas)"

:: ---- Resumen ----
echo.
echo  --- Resumen ---
if %FAILED% EQU 0 (
    echo [OK] Todas las dependencias instaladas correctamente.
    echo.
    echo  Para ejecutar el proyecto:  python main.py
) else (
    echo [!] Algunas dependencias fallaron. Revisa los mensajes arriba.
    echo     Instalalas manualmente con:  pip install ^<nombre^>
)
echo.
pause
exit /b 0

:: ---- Funcion auxiliar de instalacion ----
:install_dep
set "pkg=%~1"
set "label=%~2"
echo | set /p ="  Instalando %label%..."
python -m pip install %pkg% --quiet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo  OK
) else (
    echo  FALLO
    set /a FAILED+=1
)
exit /b
