# -*- coding: utf-8 -*-

app_name = "innexar_core"
app_title = "Innexar Core"
app_publisher = "Innexar"
app_description = "Customizações Innexar para ERP Cloud"
app_email = "dev@innexar.com"
app_license = "MIT"

# Fixtures - dados pré-carregados
fixtures = [
	{
		"dt": "SAAS Plan",
		"filters": [["name", "in", ["Básico", "Profissional", "Enterprise"]]]
	}
]

# Detecta e aplica idioma por cabeçalho/geo antes de cada requisição
# before_request = [
# 	"innexar_core.saas_management.utils.locale.detect_and_set_language",
# ]


