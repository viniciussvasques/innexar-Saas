# 🚀 Innexar ERP Cloud - Plataforma SaaS White Label

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![ERPNext](https://img.shields.io/badge/ERPNext-14.99.5-green.svg)](https://erpnext.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

> Plataforma SaaS de gestão empresarial (ERP) baseada no framework ERPNext, totalmente personalizada, multilíngue e com suporte a cobrança em dólar e real.

## 📋 Sobre o Projeto

O **Innexar ERP Cloud** é uma solução SaaS White Label que permite oferecer ERPNext como serviço, com:

- ✅ **Multi-tenancy**: Cada cliente tem seu próprio ambiente isolado (container dedicado)
- ✅ **Provisionamento Automático**: Criação de tenants com containers Docker dedicados
- ✅ **Múltiplos Planos**: Sistema de planos com módulos configuráveis
- ✅ **Billing**: Suporte para cobrança em USD e BRL
- ✅ **Multi-idioma**: Português (pt-BR) e Espanhol (es-ES) nativos
- ✅ **Branding Personalizado**: Totalmente personalizado com cores e logo da Innexar
- ✅ **Dashboard Administrativo**: Painel centralizado para gerenciar tenants, planos e billing

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Innexar Platform (Admin)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ERPNext Base + Innexar Core Module                  │  │
│  │  - Gerenciamento de Tenants                           │  │
│  │  - Gerenciamento de Planos                             │  │
│  │  - Billing & Cobrança                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Docker API
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌─────────▼─────────┐  ┌─────▼──────┐
│  Tenant 01   │  │    Tenant 02      │  │  Tenant N  │
│  (teste01)   │  │  (containerized)  │  │  (isolated)│
│              │  │                   │  │            │
│  ERPNext     │  │    ERPNext        │  │  ERPNext   │
│  + Modules   │  │    + Modules      │  │  + Modules │
│              │  │                   │  │            │
│  DB: tenant_ │  │  DB: tenant_xxx   │  │  DB: ...   │
│     teste01  │  │                   │  │            │
└──────────────┘  └───────────────────┘  └────────────┘
```

### Componentes Principais

- **Backend**: ERPNext + Frappe Framework (Python)
- **Database**: MariaDB (compartilhado, um DB por tenant)
- **Containerização**: Docker + Docker Compose
- **Cache/Fila**: Redis
- **Proxy Reverso**: Nginx (porta 80/443)
- **Orquestração**: Docker Compose (local) / Kubernetes (produção)

## 🚀 Quick Start

### Pré-requisitos

- Windows 10/11 ou Linux
- Docker Desktop (ou Docker Engine + Docker Compose)
- Git

### Instalação Local

1. **Clone o repositório**
   ```bash
   git clone https://github.com/viniciussvasques/innexar-Saas.git
   cd innexar-Saas
   ```

2. **Suba os serviços**
   ```bash
   cd innexar-platform
   docker compose up -d --build
   ```

3. **Aguarde a inicialização** (pode levar alguns minutos na primeira vez)
   ```bash
   docker compose logs -f backend
   ```

4. **Acesse o sistema**
   - **Gerenciador**: http://localhost:8000
   - **Login**: `Administrator`
   - **Senha**: `innexar_admin`

### Criando Seu Primeiro Tenant

1. Acesse o gerenciador: http://localhost:8000
2. Vá em: **Innexar SaaS** → **SAAS Tenant**
3. Clique em **Novo** e preencha:
   - Nome do Tenant: `meu-cliente`
   - Subdomínio: `meu-cliente`
   - Plano: Escolha um plano (Starter, Professional ou Enterprise)
   - Senha Admin: (opcional, será gerada automaticamente se não informada)
4. Clique em **Salvar**
5. Aguarde o provisionamento automático (você receberá uma notificação quando estiver pronto)

### Acessando o Tenant

Após o provisionamento:

- **URL**: `http://localhost:PORTA` (a porta será mostrada no registro do tenant)
- **Login**: `Administrator`
- **Senha**: A senha definida ou gerada automaticamente

## 📁 Estrutura do Projeto

```
Innexar-saas/
├── innexar-platform/          # Plataforma principal (ERPNext + Docker)
│   ├── docker/                 # Dockerfiles e entrypoints
│   ├── docker-compose.yml      # Orquestração local
│   ├── config/                 # Configurações (MariaDB, etc)
│   └── README-DEV.md           # Guia de desenvolvimento
│
├── innexar-core/               # Módulo Innexar Core (app Frappe)
│   └── innexar_core/
│       ├── saas_management/    # Módulo SaaS
│       │   ├── doctype/        # DocTypes (SAAS Plan, SAAS Tenant)
│       │   ├── models/         # Modelos de negócio
│       │   └── utils/          # Utilitários
│       └── hooks.py            # Hooks do Frappe
│
├── DOCS/                       # Documentação técnica
│   ├── 01-resumo-executivo.md
│   ├── 02-arquitetura-tecnica.md
│   ├── 03-planos-e-modulos.md
│   └── ...
│
└── scripts/                    # Scripts auxiliares
    └── create_tenant.py         # Script de criação manual de tenants
```

## 🎯 Funcionalidades

### ✅ Implementado (MVP)

- [x] Multi-tenancy com containers Docker isolados
- [x] Provisionamento automático de tenants
- [x] Gerenciamento de planos (Starter, Professional, Enterprise)
- [x] Dashboard administrativo para gerenciar tenants
- [x] Suporte a múltiplos idiomas (pt-BR, es-ES, en)
- [x] Branding personalizado (logo, cores)
- [x] Controle de status de tenants (draft, provisioning, active, suspended, cancelled)
- [x] Gerenciamento de containers (iniciar, parar, reiniciar, reconstruir)

### 🚧 Em Desenvolvimento

- [ ] Integração com Stripe/PagSeguro para pagamentos
- [ ] Automação de DNS (Cloudflare API)
- [ ] Proxy reverso com wildcard SSL (Traefik/Nginx)
- [ ] Sistema de billing completo
- [ ] Dashboard de métricas e uso
- [ ] Backups automáticos

### 📋 Planejado

- [ ] Automação completa de criação via landing page
- [ ] Sistema de notificações por email
- [ ] Suporte técnico integrado
- [ ] Escalonamento horizontal (Kubernetes)
- [ ] Monitoramento (Prometheus + Grafana)

## 📚 Documentação

A documentação completa está disponível em `DOCS/`:

- [Índice](DOCS/00-indice.md)
- [Resumo Executivo](DOCS/01-resumo-executivo.md)
- [Arquitetura Técnica](DOCS/02-arquitetura-tecnica.md)
- [Planos e Módulos](DOCS/03-planos-e-modulos.md)
- [Fluxo de Provisionamento](DOCS/04-fluxo-provisionamento.md)
- [Plano de Fases](DOCS/05-plano-fases.md)
- [Recomendações Técnicas](DOCS/06-recomendacoes-tecnicas.md)

## 🛠️ Desenvolvimento

Veja o [README-DEV.md](innexar-platform/README-DEV.md) para instruções detalhadas de desenvolvimento.

### Build da Imagem Tenant

Para rebuildar a imagem dos tenants (após alterações no `innexar-core`):

**Windows:**
```powershell
.\innexar-platform\build-tenant-image.bat
```

**Linux/Mac:**
```bash
./innexar-platform/build-tenant-image.sh
```

## 🔐 Segurança

- Cada tenant roda em um container isolado
- Bancos de dados separados por tenant
- Senhas geradas automaticamente (ou definidas manualmente)
- Docker socket com permissões restritas

⚠️ **IMPORTANTE**: Em produção, configure:
- SSL/TLS para todos os domínios
- Firewall e rate limiting
- Backups automáticos
- Monitoramento de segurança

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Contato

- **GitHub**: [@viniciussvasques](https://github.com/viniciussvasques)
- **Repositório**: https://github.com/viniciussvasques/innexar-Saas

## 🙏 Agradecimentos

- [ERPNext](https://erpnext.com/) - Framework base
- [Frappe](https://frappe.io/) - Framework Python
- Comunidade open source

---

**Desenvolvido com ❤️ pela equipe Innexar**


