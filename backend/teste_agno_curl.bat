@echo off
echo ======================================================
echo Testando o endpoint /agno/corrigir via curl
echo ======================================================

echo.
echo Testando endpoint /agno/corrigir...
curl -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"verificar\"}" http://localhost:8000/agno/corrigir

echo.
echo.
echo ======================================================
echo.
echo Testando endpoint /api/agno/corrigir...
curl -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"verificar\"}" http://localhost:8000/api/agno/corrigir

echo.
echo ======================================================
echo Teste concluído!
echo ======================================================
pause
