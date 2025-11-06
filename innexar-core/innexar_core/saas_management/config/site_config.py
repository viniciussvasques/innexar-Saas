# Configurações específicas do site base (erpBase)

def get_site_config():
    """Retorna as configurações específicas para o site base"""
    return {
        "saas": {
            "is_base_site": True,
            # Domínio base para construir FQDNs (dev: innexar.local, prod: innexar.com)
            "base_domain": "innexar.local",
            "enabled": True,
            "supported_languages": ["en", "pt-BR", "es-ES"],
            "branding": {
                "app_name": "Innexar ERP Cloud",
                "primary_color": "#1F2A44",
                "secondary_color": "#1ABC9C",
            },
            "modules": {
                "saas_management": {
                    "enabled": True,
                    "roles": ["System Manager", "SAAS Manager"],
                    "description": "Módulo de gerenciamento de tenants"
                }
            }
        }
    }

def is_base_site():
    """Verifica se o site atual é o site base"""
    import frappe
    return frappe.local.site == frappe.local.conf.get('base_site', 'erpbase.local')
