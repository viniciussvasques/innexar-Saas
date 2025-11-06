# Innexar Platform - ERP SaaS

## Visão Geral
Plataforma de gestão empresarial (ERP SaaS) baseada no Odoo, com marca própria e funcionalidades escaláveis para pequenas e médias empresas.

## Características Principais
- 🌐 **100% Web**: Acesso através de subdomínios exclusivos
- 🏢 **Multi-tenant**: Isolamento completo de dados por cliente
- 📊 **Modular**: Ativação de funcionalidades por plano
- 🎨 **Marca Própria**: Interface completamente personalizada
- ⚡ **Escalável**: Provisionamento automático de instâncias
- 💳 **Billing Integrado**: Gestão automática de planos e pagamentos

## Estrutura do Projeto

```
innexar-platform/
├── custom-addons/          # Módulos personalizados da plataforma
│   ├── innexar_base/       # Módulo base com branding
│   ├── innexar_saas/       # Gestão SaaS e multi-tenant
│   ├── innexar_billing/    # Sistema de cobrança
│   └── innexar_plans/      # Gestão de planos
├── config/                 # Configurações do sistema
├── scripts/               # Scripts de automação
├── docker/                # Configurações Docker
├── themes/                # Temas personalizados
└── deployment/            # Scripts de deploy
```

## Planos Disponíveis

| Plano | Módulos Principais | Usuários | Preço |
|-------|-------------------|----------|-------|
| **Básico** | Vendas, Clientes, Financeiro | 3 | R$ 97/mês |
| **Profissional** | + Estoque, Relatórios, Compras | 10 | R$ 197/mês |
| **Empresarial** | + RH, Projetos, Produção | 25 | R$ 397/mês |
| **Personalizado** | Módulos sob medida | Ilimitado | Sob consulta |

## Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- PostgreSQL 12+
- Node.js 14+
- Docker (opcional)

### Instalação Local
```bash
# 1. Clone o repositório
git clone [seu-repo] innexar-platform

# 2. Instale dependências Python
pip install -r requirements.txt

# 3. Configure o banco de dados
createdb innexar_master

# 4. Execute migrações
python odoo-bin -d innexar_master -i base --stop-after-init

# 5. Inicie o servidor
python odoo-bin -d innexar_master
```

### Instalação com Docker
```bash
docker-compose up -d
```

## Automação SaaS

### Criação Automática de Tenants
O sistema automatiza:
1. Criação de subdomínio (cliente.innexar.com)
2. Provisionamento de banco de dados dedicado
3. Instalação de módulos conforme plano
4. Configuração de usuário administrador
5. Envio de credenciais por e-mail

### Gestão de Billing
- Integração com Stripe/PayPal
- Cobrança recorrente automática
- Upgrade/downgrade de planos
- Suspensão por inadimplência
- Relatórios financeiros

## Personalização da Marca

### Elementos Customizáveis
- ✅ Logotipo e favicon
- ✅ Paleta de cores
- ✅ Tipografia
- ✅ Layout e componentes
- ✅ E-mails transacionais
- ✅ URLs e subdomínios

### Remoção Completa do Branding Odoo
- Substituição de todas as referências
- Logo personalizado em todas as telas
- Rodapé e links próprios
- Documentação e ajuda personalizadas

## Módulos Principais

### Core SaaS (`innexar_saas`)
- Gestão multi-tenant
- Provisionamento automático
- Isolamento de dados
- Gerenciamento de subdomínios

### Billing (`innexar_billing`)
- Planos e preços
- Processamento de pagamentos
- Faturas e cobranças
- Métricas de receita

### Base Platform (`innexar_base`)
- Branding personalizado
- Configurações globais
- Templates de e-mail
- Políticas de segurança

## Roadmap

### Fase 1 - Core Platform ✅
- [x] Estrutura base do projeto
- [x] Customização visual inicial
- [ ] Módulos SaaS básicos
- [ ] Sistema de multi-tenancy

### Fase 2 - Automação
- [ ] Provisionamento automático
- [ ] Integração de pagamentos
- [ ] Portal de assinatura
- [ ] E-mails transacionais

### Fase 3 - Escalabilidade
- [ ] Kubernetes deployment
- [ ] Monitoramento avançado
- [ ] Backup automático
- [ ] CDN e performance

### Fase 4 - Marketplace
- [ ] Loja de apps
- [ ] API pública
- [ ] Integrações third-party
- [ ] White-label partners

## Suporte e Documentação

- 📚 [Documentação Técnica](docs/)
- 🎯 [Guia de Implementação](docs/implementation.md)
- 🔧 [API Reference](docs/api.md)
- 💬 [Suporte Técnico](mailto:suporte@innexar.com)

## Licença

Projeto proprietário - Todos os direitos reservados © 2025 Innexar Platform