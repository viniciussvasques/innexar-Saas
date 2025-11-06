# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe

def get_hooks():
    # Verifica se é o site base (erpBase)
    if not frappe.local.site == frappe.local.conf.get('base_site'):
        return {}
        
    return {
        "app_name": "saas_management",
        "app_title": "SaaS Management",
        "app_description": "Gerenciamento de multi-tenancy para ERPNext",
        "app_publisher": "Innexar",
        "app_email": "contato@innexar.com.br",
        "app_license": "MIT",
        "app_version": "1.0.0",
        "category": "Administration",
        "icon": "fa fa-cubes",
        "color": "#3498db",
        "is_published": False,  # Não listado no marketplace
        "only_for_base_site": True,  # Apenas para o site base
        "on_install": "saas_management.setup.install.install",
        "on_uninstall": "saas_management.setup.uninstall.uninstall",
        "on_migrate": "saas_management.setup.migrate.migrate",
        "include_js": {
            "www/saas_management.js": "List/SaaS Tenant"
        },
        "scheduler_events": {
            "all": ["saas_management.api.sync_tenants"],
            "daily": ["saas_management.api.check_quotas"],
            "hourly": ["saas_management.api.cleanup_old_containers"]
        },
        "permission_query_conditions": {
            "SAAS Plan": "saas_management.permission.get_permission_query_conditions",
            "SAAS Tenant": "saas_management.permission.get_permission_query_conditions"
        },
        "required_apps": ["erpnext"],
        "required_roles": ["System Manager", "SAAS Manager"]
    }
