// Copyright (c) 2025, Innexar and contributors
// For license information, please see license.txt

frappe.ui.form.on("SAAS Tenant", {
	refresh: function(frm) {
		// Botões de gerenciamento do container
		if (!frm.is_new()) {
			// Botão para reconstruir container
			if (frm.doc.subdomain) {
				frm.add_custom_button(__("Reconstruir Container"), function() {
					frappe.confirm(
						__("Tem certeza que deseja reconstruir o container? O container atual será removido e um novo será criado."),
						function() {
							// Yes
							frappe.call({
								method: "innexar_core.saas_management.doctype.saas_tenant.saas_tenant.recreate_tenant_container",
								args: {
									tenant_name: frm.doc.name
								},
								freeze: true,
								freeze_message: __("Reconstruindo container..."),
								callback: function(r) {
									if (r.message && r.message.status === "success") {
										frappe.show_alert({
											message: __("Container reconstruído com sucesso!"),
											indicator: "green"
										}, 5);
										frm.reload_doc();
									} else {
										frappe.show_alert({
											message: __("Erro ao reconstruir container: {0}", [r.message?.message || "Erro desconhecido"]),
											indicator: "red"
										}, 5);
									}
								}
							});
						},
						function() {
							// No - não faz nada
						}
					);
				}, __("Container"));
			}

			// Botão para sincronizar informações do container
			if (frm.doc.subdomain) {
				frm.add_custom_button(__("Sincronizar Container"), function() {
					frappe.call({
						method: "innexar_core.saas_management.doctype.saas_tenant.saas_tenant.sync_container_info",
						args: {
							tenant_name: frm.doc.name
						},
						freeze: true,
						freeze_message: __("Sincronizando informações do container..."),
						callback: function(r) {
							if (r.message) {
								frappe.show_alert({
									message: __("Informações sincronizadas!"),
									indicator: "green"
								}, 3);
								frm.reload_doc();
							}
						}
					});
				}, __("Container"));
			}

			// Botões de controle do container (se existir)
			if (frm.doc.container_name || frm.doc.subdomain) {
				const container_name = frm.doc.container_name || frm.doc.subdomain;
				
				// Botão para reiniciar
				frm.add_custom_button(__("Reiniciar"), function() {
					frappe.call({
						method: "innexar_core.saas_management.doctype.saas_tenant.saas_tenant.restart_tenant_container",
						args: {
							tenant_name: frm.doc.name
						},
						callback: function(r) {
							if (r.message && r.message.status === "success") {
								frappe.show_alert({
									message: __("Container reiniciado!"),
									indicator: "green"
								}, 3);
								frm.reload_doc();
							} else {
								frappe.show_alert({
									message: __("Erro: {0}", [r.message?.message || "Erro desconhecido"]),
									indicator: "red"
								}, 5);
							}
						}
					});
				}, __("Container"));

				// Botão para iniciar
				if (frm.doc.container_status !== "running") {
					frm.add_custom_button(__("Iniciar"), function() {
						frappe.call({
							method: "innexar_core.saas_management.doctype.saas_tenant.saas_tenant.start_tenant_container",
							args: {
								tenant_name: frm.doc.name
							},
							callback: function(r) {
								if (r.message && r.message.status === "success") {
									frappe.show_alert({
										message: __("Container iniciado!"),
										indicator: "green"
									}, 3);
									frm.reload_doc();
								} else {
									frappe.show_alert({
										message: __("Erro: {0}", [r.message?.message || "Erro desconhecido"]),
										indicator: "red"
									}, 5);
								}
							}
						});
					}, __("Container"));
				}

				// Botão para parar
				if (frm.doc.container_status === "running") {
					frm.add_custom_button(__("Parar"), function() {
						frappe.call({
							method: "innexar_core.saas_management.doctype.saas_tenant.saas_tenant.stop_tenant_container",
							args: {
								tenant_name: frm.doc.name
							},
							callback: function(r) {
								if (r.message && r.message.status === "success") {
									frappe.show_alert({
										message: __("Container parado!"),
										indicator: "orange"
									}, 3);
									frm.reload_doc();
								} else {
									frappe.show_alert({
										message: __("Erro: {0}", [r.message?.message || "Erro desconhecido"]),
										indicator: "red"
									}, 5);
								}
							}
						});
					}, __("Container"));
				}

				// Botão para remover container
				frm.add_custom_button(__("Remover Container"), function() {
					frappe.confirm(
						__("Tem certeza que deseja remover o container? Esta ação não pode ser desfeita."),
						function() {
							// Yes
							frappe.call({
								method: "innexar_core.saas_management.doctype.saas_tenant.saas_tenant.delete_tenant_container",
								args: {
									tenant_name: frm.doc.name
								},
								freeze: true,
								freeze_message: __("Removendo container..."),
								callback: function(r) {
									if (r.message && r.message.status === "success") {
										frappe.show_alert({
											message: __("Container removido!"),
											indicator: "green"
										}, 3);
										frm.reload_doc();
									} else {
										frappe.show_alert({
											message: __("Erro: {0}", [r.message?.message || "Erro desconhecido"]),
											indicator: "red"
										}, 5);
									}
								}
							});
						}
					);
				}, __("Container"));
			}

			// Botão para acessar URL do tenant
			if (frm.doc.access_url) {
				frm.add_custom_button(__("Abrir Tenant"), function() {
					window.open(frm.doc.access_url, "_blank");
				}, __("Ações"));
			}
		}
	}
});


