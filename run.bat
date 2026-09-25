@echo off
setlocal enabledelayedexpansion
title Gestao Estrategica de Demandas Juridicas - Streamlit

echo ======================================================================
echo   GESTAO ESTRATEGICA E OPERACIONAL DE DEMANDAS JURIDICAS
echo ======================================================================
echo.

set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

:: 1. Tentar localizar o interpretador Python
set "PYTHON_EXE="

:: Verifica se existe venv na propria pasta
if exist "%BASE_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%BASE_DIR%venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

:: Verifica se existe o venv do Gestao_Adm
if exist "F:\SistemaGestao\Gestao_Adm\venv\Scripts\python.exe" (
    set "PYTHON_EXE=F:\SistemaGestao\Gestao_Adm\venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

:: Tenta python no PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    for /f "delims=" %%I in ('where python') do (
        set "PYTHON_EXE=%%I"
        goto :PYTHON_FOUND
    )
)

:PYTHON_FOUND
if "%PYTHON_EXE%"=="" (
    echo [ERRO] Python nao foi encontrado no sistema!
    echo Por favor, instale o Python ou configure o ambiente virtual.
    echo.
    pause
    exit /b 1
)

echo [OK] Python localizado: "%PYTHON_EXE%"
echo.

:: 2. Verificar se o Streamlit esta instalado
echo [INFO] Verificando dependencias essenciais...
"%PYTHON_EXE%" -c "import streamlit, plotly, pandas, sqlalchemy" >nul 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Dependencias ausentes detectadas.
    echo Instalando pacotes necessarios de requirements.txt...
    echo Isso pode levar alguns minutos na primeira execucao...
    "%PYTHON_EXE%" -m pip install --upgrade pip
    "%PYTHON_EXE%" -m pip install -r "%BASE_DIR%requirements.txt"
    if %errorlevel% neq 0 (
        echo.
        echo [ERRO] Falha ao instalar as dependencias via pip.
        echo Verifique os erros acima e sua conexao de rede.
        pause
        exit /b 1
    )
    echo [OK] Todas as dependencias foram instaladas com sucesso!
) else (
    echo [OK] Dependencias verificadas com sucesso!
)

echo.
echo ======================================================================
echo [INICIANDO] Executando servidor Streamlit...
echo Acesse no navegador: http://localhost:8501
echo Para encerrar, feche esta janela ou pressione Ctrl+C.
echo ======================================================================
echo.

"%PYTHON_EXE%" -m streamlit run "%BASE_DIR%app.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu uma falha ao executar a aplicacao Streamlit.
    pause
)
