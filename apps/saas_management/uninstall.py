# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe

def before_uninstall():
    """Executado antes da desinstalação do módulo"""
    # Verifica se existem tenants ativos
    active_tenants = frappe.get_all("SAAS Tenant", 
                                  filters={"container_status": ["!=", "not_created"]},
                                  limit=1)
    
    if active_tenants:
        frappe.throw("Não é possível desinstalar o módulo com tenants ativos. Por favor, remova todos os tenants antes de desinstalar.")
    
    # Remove os planos padrão
    remove_default_plans()
    
    # Remove as funções personalizadas
    remove_roles()
    
    frappe.msgprint("Módulo SaaS Management desinstalado com sucesso!")

def remove_default_plans():
    """Remove os planos padrão"""
    default_plans = ["BASIC", "PRO", "ENTERPRISE"]
    for plan_code in default_plans:
        if frappe.db.exists("SAAS Plan", {"code": plan_code}):
            frappe.delete_doc("SAAS Plan", plan_code, ignore_permissions=True)

def remove_roles():
    """Remove as funções personalizadas"""
    roles = ["SAAS Manager", "SAAS User"]
    for role in roles:
        if frappe.db.exists("Role", role):
            frappe.delete_doc("Role", role, ignore_permissions=True)

def after_uninstall():
    """Executado após a desinstalação do módulo"""
    # Limpa quaisquer dados residuais
    frappe.clear_cache()
