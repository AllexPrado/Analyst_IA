@echo off
echo ===================================================
echo Teste de Endpoints Agno - Verificacao Rapida
echo ===================================================

echo.
echo Testando /agno/corrigir...
curl -s -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"corrigir\"}" http://localhost:8000/agno/corrigir
echo.
echo.

echo Testando /api/agno/corrigir...
curl -s -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"corrigir\"}" http://localhost:8000/api/agno/corrigir
echo.
echo.

echo Testando /agno/feedback...
curl -s -X POST -H "Content-Type: application/json" -d "{\"feedback\":{\"tipo\":\"teste\",\"mensagem\":\"teste\"}}" http://localhost:8000/agno/feedback
echo.
echo.

echo ===================================================
echo Teste concluido!
echo ===================================================

pause
