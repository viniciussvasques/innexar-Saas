# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def after_install():
    """Executado após a instalação do módulo"""
    create_roles()
    create_default_plans()
    frappe.msgprint(_("Módulo SaaS Management instalado com sucesso!"))

def create_roles():
    """Cria as funções de usuário necessárias"""
    roles = [
        {
            "doctype": "Role",
            "role_name": "SAAS Manager",
            "desk_access": 1,
            "is_custom": 1,
            "role_type": "System Manager",
            "restrict_to_domain": ""
        },
        {
            "doctype": "Role",
            "role_name": "SAAS User",
            "desk_access": 1,
            "is_custom": 1,
            "role_type": "User",
            "restrict_to_domain": ""
        }
    ]
    
    for role in roles:
        if not frappe.db.exists("Role", role["role_name"]):
            frappe.get_doc(role).insert(ignore_permissions=True)

def create_default_plans():
    """Cria planos padrão se não existirem"""
    default_plans = [
        {
            "doctype": "SAAS Plan",
            "plan_name": "Básico",
            "code": "BASIC",
            "price_monthly": 99.90,
            "price_yearly": 999.00,
            "max_users": 5,
            "max_storage_gb": 10,
            "dedicated_container": False,
            "cpu_cores": 1,
            "memory_gb": 2,
            "module_inventory": True,
            "module_accounting": True,
            "module_hr": False,
            "module_project": False
        },
        {
            "doctype": "SAAS Plan",
            "plan_name": "Profissional",
            "code": "PRO",
            "price_monthly": 199.90,
            "price_yearly": 1999.00,
            "max_users": 20,
            "max_storage_gb": 50,
            "dedicated_container": False,
            "cpu_cores": 2,
            "memory_gb": 4,
            "module_inventory": True,
            "module_accounting": True,
            "module_hr": True,
            "module_project": True
        },
        {
            "doctype": "SAAS Plan",
            "plan_name": "Empresarial",
            "code": "ENTERPRISE",
            "price_monthly": 499.90,
            "price_yearly": 4999.00,
            "max_users": 100,
            "max_storage_gb": 200,
            "dedicated_container": True,
            "cpu_cores": 4,
            "memory_gb": 8,
            "module_inventory": True,
            "module_accounting": True,
            "module_hr": True,
            "module_project": True
        }
    ]
    
    for plan_data in default_plans:
        if not frappe.db.exists("SAAS Plan", {"code": plan_data["code"]}):
            frappe.get_doc(plan_data).insert(ignore_permissions=True)

def after_migrate():
    """Executado após a migração do banco de dados"""
    # Atualiza permissões e configurações pós-migração
    pass
