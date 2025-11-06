# Recomendações Técnicas e Operação

Infraestrutura:

- VPS mínimo: 8 GB RAM e 4 CPUs
- Backups automáticos diários (banco e volumes)
- Monitoramento: Prometheus + Grafana; Logs centralizados; Sentry para erros
- Atualizações periódicas do ERPNext com app custom separado

Segurança:

- TLS (Cloudflare/Origin) e proxy_mode habilitado
- db_filter por subdomínio/site
- Rotação de credenciais sensíveis
- Políticas de backup/restore testadas

Billing e assinatura:

- Testar billing, renovação e cancelamento
- Webhooks de Stripe/PagSeguro para ativação/suspensão
- Métricas de uso por tenant (painel admin)

Onboarding:

- Tutoriais/vídeos de ativação
- Templates de e-mail transacionais


