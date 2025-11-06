#!/bin/bash
# Script para buildar a imagem Docker tenant com innexar_core incluído

set -e

echo "=== Building Innexar Tenant Image with innexar_core ==="

# Define o diretório raiz do projeto
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Verifica se o diretório innexar-core existe
if [ ! -d "innexar-core" ]; then
    echo "ERRO: Diretório innexar-core não encontrado!"
    echo "Certifique-se de que o projeto está na estrutura correta:"
    echo "  - innexar-platform/"
    echo "  - innexar-core/"
    exit 1
fi

# Builda a imagem base primeiro (se necessário)
echo "1. Verificando imagem base..."
if ! docker images | grep -q "innexar-platform-backend.*latest"; then
    echo "   Imagem base não encontrada. Buildando..."
    cd innexar-platform
    docker build -f docker/backend/Dockerfile -t innexar-platform-backend:latest .
    cd ..
else
    echo "   Imagem base encontrada."
fi

# Builda a imagem tenant com innexar_core
echo "2. Buildando imagem tenant com innexar_core..."
# Builda a partir da raiz do projeto para que o COPY funcione
docker build \
    -f innexar-platform/docker/backend/Dockerfile.tenant \
    -t innexar-platform-backend:tenant \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

echo ""
echo "=== Imagem tenant buildada com sucesso! ==="
echo "Imagem: innexar-platform-backend:tenant"
echo ""
echo "Para usar esta imagem, configure a variável de ambiente:"
echo "  export INNEXAR_CORE_IMAGE=innexar-platform-backend:tenant"
echo ""
echo "Ou edite o arquivo saas_tenant.py para usar esta imagem por padrão."

