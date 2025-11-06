try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover
    frappe = None  # allows import-time in non-frappe context


def apply_brand_and_languages(languages: list[str] | None = None, default_language: str | None = None, app_name: str | None = None) -> dict:
    """Aplica configurações de brand e idiomas no site atual.

    - Seta idioma padrão (System Settings + default)
    - Ajusta título do website
    - Ajusta web_app_name usado no login
    """
    if frappe is None:
        return {"status": "error", "message": "frappe not available"}

    try:
        frappe.only_for("System Manager") if hasattr(frappe, "only_for") else None

        # Habilitar idiomas desejados no DocType Language
        if languages:
            for code in languages:
                try:
                    lang_doc = frappe.get_doc("Language", code)
                    if not lang_doc.enabled:
                        lang_doc.enabled = 1
                        lang_doc.save()
                except Exception:
                    # cria registro se não existir
                    try:
                        frappe.get_doc({
                            "doctype": "Language",
                            "name": code,
                            "language_code": code,
                            "enabled": 1,
                        }).insert(ignore_permissions=True)
                    except Exception:
                        pass

        if default_language:
            # Idioma padrão do sistema
            frappe.db.set_value("System Settings", "System Settings", "language", default_language)
            frappe.db.set_default("lang", default_language)

        if app_name:
            # Título do website
            try:
                frappe.db.set_value("Website Settings", "Website Settings", "website_title", app_name)
            except Exception:
                pass
            # Nome do app exibido (login/web)
            frappe.db.set_value("ir_config_parameter", "web.web_app_name", "value", app_name)

        # Observação: lista de idiomas suportados pode exigir instalação de traduções
        # Em ERPNext/Frappe, as traduções de pt-BR e es-ES já existem nos pacotes.

        frappe.db.commit()
        return {"status": "success"}
    except Exception as e:  # pragma: no cover
        frappe.db.rollback()
        return {"status": "error", "message": str(e)}


