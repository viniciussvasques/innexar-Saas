# Script para configurar o ambiente de desenvolvimento do ERPNext

# Configurações
$FRAPPE_BRANCH = "version-14"
$ERPNEXT_BRANCH = "version-14"
$BENCH_PATH = "$PWD/bench"

# Função para executar comandos e verificar erros
function Invoke-CommandWithCheck {
    param (
        [string]$Command,
        [string]$ErrorMessage = "Erro ao executar o comando: $Command"
    )
    
    Write-Host "Executando: $Command" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    Invoke-Expression $Command
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host $ErrorMessage -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Verificar se o Git está instalado
try {
    git --version | Out-Null
} catch {
    Write-Host "Git não encontrado. Por favor, instale o Git e tente novamente." -ForegroundColor Red
    exit 1
}

# Verificar se o Python 3.10+ está instalado
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3.10" -or $pythonVersion -match "Python 3.1[1-9]") {
        Write-Host "Python 3.10+ encontrado: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "Python 3.10+ não encontrado. Por favor, instale o Python 3.10 ou superior." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Python não encontrado. Por favor, instale o Python 3.10 ou superior." -ForegroundColor Red
    exit 1
}

# Instalar o pip se não estiver instalado
try {
    python -m pip --version | Out-Null
} catch {
    Write-Host "Instalando pip..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
}

# Instalar o Bench CLI
Write-Host "Instalando o Bench CLI..." -ForegroundColor Yellow
python -m pip install --user frappe-bench

# Adicionar o diretório de scripts do Python ao PATH
$pythonPath = python -c "import site; print(site.USER_BASE)"
$pythonScriptsPath = Join-Path $pythonPath "Scripts"
$env:Path += ";$pythonScriptsPath"

# Verificar se o bench está instalado
try {
    bench --version | Out-Null
} catch {
    Write-Host "Bench não encontrado no PATH. Por favor, adicione $pythonScriptsPath ao seu PATH e tente novamente." -ForegroundColor Red
    exit 1
}

# Criar diretório para o bench
if (-not (Test-Path $BENCH_PATH)) {
    New-Item -ItemType Directory -Path $BENCH_PATH | Out-Null
}

# Inicializar o ambiente bench
Write-Host "Inicializando o ambiente bench..." -ForegroundColor Yellow
Set-Location $BENCH_PATH
bench init --skip-redis-config-generation --frappe-branch $FRAPPE_BRANCH --python python3.10 --skip-assets --verbose frappe-bench

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao inicializar o ambiente bench." -ForegroundColor Red
    exit 1
}

# Navegar para o diretório do bench
Set-Location frappe-bench

# Clonar o repositório do ERPNext
if (-not (Test-Path "apps/erpnext")) {
    Write-Host "Clonando o repositório do ERPNext..." -ForegroundColor Yellow
    git clone --depth 1 --branch $ERPNEXT_BRANCH https://github.com/frappe/erpnext.git apps/erpnext
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro ao clonar o repositório do ERPNext." -ForegroundColor Red
        exit 1
    }
}

# Instalar o ERPNext
Write-Host "Instalando o ERPNext..." -ForegroundColor Yellow
bench get-app erpnext ./apps/erpnext

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao instalar o ERPNext." -ForegroundColor Red
    exit 1
}

# Criar um novo site
$SITE_NAME = "innexar.local"
Write-Host "Criando o site $SITE_NAME..." -ForegroundColor Yellow
bench new-site $SITE_NAME --db-name innexar --db-password innexar_pass --admin-password innexar_admin --mariadb-root-username root --mariadb-root-password innexar_root_pass --install-app erpnext

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao criar o site." -ForegroundColor Red
    exit 1
}

# Iniciar o servidor de desenvolvimento
Write-Host "Configuração concluída com sucesso!" -ForegroundColor Green
Write-Host "Para iniciar o servidor de desenvolvimento, execute:" -ForegroundColor Green
Write-Host "cd $BENCH_PATH\frappe-bench && bench start" -ForegroundColor Yellow
