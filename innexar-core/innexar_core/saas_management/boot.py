# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from .config.site_config import is_base_site

def boot_session(bootinfo):
    """Adiciona informações à sessão do usuário"""
    # Verifica se é o site base
    if not is_base_site():
        return
        
    # Adiciona informações específicas do módulo
    bootinfo.saas_management = {
        "version": "1.0.0",
        "api_version": "v1",
        "base_url": "/api/method/saas_management.api",
        "is_base_site": True
    }
    
    # Adiciona permissões ao usuário
    if frappe.session.user != "Guest":
        # Verifica se o usuário tem permissão para acessar o módulo
        has_permission = frappe.has_permission("SAAS Settings")
        bootinfo.user_can_manage_saas = has_permission
        
        if has_permission:
            # Adiciona links rápidos para administradores
            bootinfo.saas_management["quick_actions"] = [
                {"label": "Criar Novo Tenant", "action": "saas_management.create_tenant"},
                {"label": "Gerenciar Planos", "action": "saas_management.manage_plans"},
                {"label": "Relatórios", "action": "saas_management.reports"}
            ]
            
            # Adiciona informações do tenant à sessão
            bootinfo.saas_management.update({
                'is_saas_enabled': True,
                'max_users': frappe.get_system_settings("max_users") or 1,
                'max_storage': frappe.get_system_settings("max_storage") or 1,
                'modules': get_enabled_modules()
            })

def get_enabled_modules():
    # Retorna a lista de módulos habilitados para o tenant
    return [m.module_name for m in frappe.get_all("Module Def", filters={"app_name": "saas_management"}, fields=["module_name"])]
