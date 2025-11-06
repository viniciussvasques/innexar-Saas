# Visão Geral do Projeto Innexar ERP Cloud

## 1. Objetivo
Implementar uma plataforma SaaS de gestão empresarial baseada no ERPNext, com suporte a multi-tenancy, cobrança em múltiplas moedas e ativação modular de recursos.

## 2. Pilares Técnicos
- **ERPNext**: Framework base para o ERP
- **Docker**: Containerização dos ambientes
- **Kubernetes**: Orquestração (futuro)
- **Stripe/PagSeguro**: Processamento de pagamentos
- **Cloudflare**: Gerenciamento de DNS e CDN
- **Python**: Automações e scripts

## 3. Estrutura de Diretórios
```
innexar-saas/
├── innexar-core/         # Código-fonte personalizado
├── innexar-platform/     # Configurações de infraestrutura
├── docs/                 # Documentação técnica
└── scripts/             # Scripts de automação
```
