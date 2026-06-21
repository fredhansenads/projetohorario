@echo off
cd /d "%~dp0"
set HOST=0.0.0.0
set PORT=8000
echo Iniciando Sistema de Horarios em modo rede na porta %PORT%
echo Acesse por http://IP-DESTE-COMPUTADOR:%PORT%
python app.py
