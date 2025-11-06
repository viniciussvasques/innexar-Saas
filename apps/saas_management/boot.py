# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe

def boot_session(bootinfo):
    # Adiciona informações do tenant à sessão
    if frappe.session.user != 'Guest':
        bootinfo.saas_management = {
            'is_saas_enabled': True,
            'max_users': frappe.get_system_settings("max_users") or 1,
            'max_storage': frappe.get_system_settings("max_storage") or 1,
            'modules': get_enabled_modules()
        }

def get_enabled_modules():
    # Retorna a lista de módulos habilitados para o tenant
    return [m.module_name for m in frappe.get_all("Module Def", filters={"app_name": "saas_management"}, fields=["module_name"])]
