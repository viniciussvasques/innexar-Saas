# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe

def get_hooks():
    # Verifica se é o site base (erpBase)
    if not frappe.local.site == frappe.local.conf.get('base_site'):
        return {}
        
    return {
        # Hooks para o módulo de gerenciamento
        'has_permission': 'saas_management.permission.has_permission',
        'on_session_creation': 'saas_management.api.create_session',
        'on_logout': 'saas_management.api.clear_session',
        
        # Eventos agendados
        'scheduler_events': {
            "daily": [
                "saas_management.utils.background_tasks.daily_backup",
                "saas_management.utils.background_tasks.check_tenant_quotas"
            ],
            "daily_long": [
                "saas_management.utils.background_tasks.cleanup_old_backups"
            ]
        },
        
        # Configurações de inicialização
        'bootstrap': 'saas_management.boot.bootstrap',
        
        # Permissões e autenticação
        'authenticate': 'saas_management.api.authenticate',
        'auth_hooks': ['saas_management.auth.validate_tenant'],
        
        # Configurações de site
        'site_config': {
            'saas': {
                'enabled': True,
                'base_domain': frappe.local.conf.get('base_domain', 'innexar.com.br')
            }
        },
        
        # Configurações de API
        'api': {
            'base_path': '/api/method/saas_management.api',
            'whitelisted_methods': [
                'saas_management.api.get_plans',
                'saas_management.api.get_tenant_status'
            ]
        }
    }
