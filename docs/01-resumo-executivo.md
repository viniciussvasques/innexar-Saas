# Resumo Executivo – Innexar ERP Cloud

O Innexar é uma plataforma SaaS de ERP baseada no ERPNext/Frappe, multilíngue e com cobrança em USD e BRL. O objetivo é ofertar uma solução escalável e modular, permitindo contratação online, provisionamento automático com subdomínio exclusivo e ativação de módulos por plano.

Principais pontos:

- Plataforma: ERPNext + Frappe
- Infraestrutura: Docker (Kubernetes futuramente)
- Multi-tenant com isolamento: container e banco MariaDB por cliente (conforme stack atual)
- DNS e proxy: Cloudflare + NGINX/Traefik com wildcard/subdomínios
- Cobrança: Stripe (EUA) e PagSeguro (Brasil)
- Automação: scripts Python para criação/remoção de tenants
- Base Admin: controle de clientes, planos, billing, métricas e suporte

Benefícios:

- Escalabilidade horizontal (novos tenants via automação)
- Time-to-value rápido (instâncias ativas imediatamente após pagamento)
- Modularidade (módulos por plano)
- White-label (branding Innexar por padrão)

Escopo inicial contempla MVP, Beta e Produção, com evolução de orquestração, automação de DNS, painel administrativo e integrações de pagamento.

