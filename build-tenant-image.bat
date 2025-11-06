@echo off
REM Script Windows para buildar a imagem Docker tenant com innexar_core incluído

echo === Building Innexar Tenant Image with innexar_core ===

REM Define o diretório raiz do projeto
cd /d "%~dp0\.."
set PROJECT_ROOT=%CD%

REM Verifica se o diretório innexar-core existe
if not exist "innexar-core" (
    echo ERRO: Diretório innexar-core não encontrado!
    echo Certifique-se de que o projeto está na estrutura correta:
    echo   - innexar-platform/
    echo   - innexar-core/
    exit /b 1
)

REM Builda a imagem base primeiro (se necessário)
echo 1. Verificando imagem base...
docker images | findstr "innexar-platform-backend.*latest" >nul
if errorlevel 1 (
    echo    Imagem base não encontrada. Buildando...
    cd innexar-platform
    docker build -f docker/backend/Dockerfile -t innexar-platform-backend:latest .
    cd ..
) else (
    echo    Imagem base encontrada.
)

REM Builda a imagem tenant com innexar_core
echo 2. Buildando imagem tenant com innexar_core...
REM Builda a partir da raiz do projeto para que o COPY funcione
docker build -f innexar-platform/docker/backend/Dockerfile.tenant -t innexar-platform-backend:tenant .

echo.
echo === Imagem tenant buildada com sucesso! ===
echo Imagem: innexar-platform-backend:tenant
echo.
echo Para usar esta imagem, configure a variável de ambiente:
echo   set INNEXAR_CORE_IMAGE=innexar-platform-backend:tenant
echo.
echo Ou edite o arquivo saas_tenant.py para usar esta imagem por padrão.

pause

