try:
    import frappe  # type: ignore
except Exception:
    frappe = None


LATAM_ES = {
    "AR", "BO", "CL", "CO", "CR", "CU", "DO", "EC", "SV", "GT", "HN",
    "MX", "NI", "PA", "PE", "PR", "PY", "UY", "VE", "ES"
}


def detect_and_set_language():
    """Define o idioma da sessão com base em Accept-Language ou país (CF-IPCountry).

    - Se Accept-Language inclui pt, usa pt-BR.
    - Se Accept-Language inclui es, usa es-ES.
    - Caso contrário, tenta país pelo header (Cloudflare) e mapeia BR→pt-BR, LatAm→es-ES.
    - Fallback: en.
    """
    if frappe is None:
        return

    try:
        req_lang = (frappe.get_request_header("Accept-Language") or "").lower()
        country = (frappe.get_request_header("CF-IPCountry") or "").upper()

        lang = "en"
        if "pt" in req_lang:
            lang = "pt-BR"
        elif "es" in req_lang:
            lang = "es-ES"
        elif country == "BR":
            lang = "pt-BR"
        elif country in LATAM_ES:
            lang = "es-ES"

        # aplica no contexto atual
        frappe.local.lang = lang
        try:
            frappe.db.set_default("lang", lang)
        except Exception:
            pass
    except Exception:
        # Nunca bloquear requisições por erro de detecção
        pass


