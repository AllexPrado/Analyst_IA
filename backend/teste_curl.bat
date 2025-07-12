@echo off
echo ===================================================
echo TESTE DO ENDPOINT /agno/corrigir
echo ===================================================
echo.

echo Testando /agno/corrigir...
curl -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"verificar\"}" http://localhost:8000/agno/corrigir
echo.
echo.

echo Testando /api/agno/corrigir para comparação...
curl -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"verificar\"}" http://localhost:8000/api/agno/corrigir
echo.
echo.

echo ===================================================
echo.
pause
