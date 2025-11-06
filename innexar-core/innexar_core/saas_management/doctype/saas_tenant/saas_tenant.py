# Copyright (c) 2025, Innexar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import docker
import json
import random
import string
import time
import os
from datetime import datetime
from innexar_core.saas_management.utils.bench_exec import bench_new_site, bench_install_app, run_bench

BACKEND_CONTAINER_NAME = os.environ.get("BACKEND_CONTAINER_NAME", "innexar-backend")
# Usa a imagem tenant que já inclui o innexar_core nativamente
CORE_IMAGE_NAME = os.environ.get("INNEXAR_CORE_IMAGE", "innexar-platform-backend:tenant")
MYSQL_ROOT_PASSWORD = os.environ.get("MYSQL_ROOT_PASSWORD", "innexar_root_pass")
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "innexar_admin")


class SAASTenant(Document):
    def validate(self):
        self.validate_subdomain()
        self.validate_plan()
    
    def validate_subdomain(self):
        # Remove caracteres inválidos do subdomínio
        import re
        self.subdomain = re.sub(r'[^a-z0-9-]', '', self.subdomain.lower())
        
        # Verifica se o subdomínio já existe
        if frappe.db.exists("SAAS Tenant", {"subdomain": self.subdomain, "name": ["!=", self.name]}):
            frappe.throw(f"O subdomínio {self.subdomain} já está em uso. Por favor, escolha outro.")
    
    def validate_plan(self):
        if not frappe.db.exists("SAAS Plan", self.plan):
            frappe.throw("O plano selecionado não existe.")
    
    def before_save(self):
        # Define tenant_name se não estiver definido (usado para autoname)
        # IMPORTANTE: tenant_name deve ser definido ANTES do save para o autoname funcionar
        if not self.tenant_name:
            if self.subdomain:
                self.tenant_name = self.subdomain
            elif self.name and self.name != 'New SAAS Tenant':
                self.tenant_name = self.name
            else:
                # Se não tem nome ainda, gera um temporário
                import uuid
                self.tenant_name = f"tenant-{uuid.uuid4().hex[:8]}"
        
        # GARANTE que container_name sempre seja o subdomínio (não pode ser "backend" ou outro valor)
        if self.subdomain:
            old_container_name = self.container_name
            # Se container_name está diferente do subdomínio, corrige
            if old_container_name and old_container_name != self.subdomain:
                # Verifica se o container com o nome correto (subdomínio) existe
                try:
                    import docker
                    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
                    # Tenta encontrar pelo subdomínio (nome correto)
                    try:
                        correct_container = client.containers.get(self.subdomain)
                        # Se encontrou pelo subdomínio, atualiza
                        self.container_name = self.subdomain
                        self.container_id = correct_container.id
                        frappe.log_error(f"Container_name corrigido de '{old_container_name}' para '{self.subdomain}'", "Docker Fix")
                    except docker.errors.NotFound:
                        # Container com nome correto não existe - limpa campos
                        self.container_name = None
                        self.container_id = None
                        frappe.log_error(f"Container {self.subdomain} não encontrado, campos limpos", "Docker Cleanup")
                except:
                    # Se não conseguir verificar, força usar subdomínio
                    self.container_name = self.subdomain
            
            # Se container_name não está definido mas subdomínio está, usa subdomínio
            if not self.container_name and self.subdomain:
                self.container_name = self.subdomain
            
            # FORÇA: container_name deve SEMPRE ser igual ao subdomain (não pode ser "backend" ou outro)
            if self.subdomain and self.container_name != self.subdomain:
                frappe.log_error(f"Corrigindo container_name de '{self.container_name}' para '{self.subdomain}'", "Docker Fix")
                self.container_name = self.subdomain
        
        if not self.admin_password:
            self.admin_password = self.generate_password()
    
    def after_insert(self):
        # CRÍTICO: Garante que o documento está salvo no banco ANTES de tentar criar o container
        # Isso garante que o tenant aparecerá na lista mesmo se a criação do container falhar
        try:
            # Garante que tenant_name está definido (necessário para autoname)
            if not self.tenant_name:
                self.tenant_name = self.subdomain or self.name
            
            # Garante valores padrão
            if not self.state:
                self.state = 'draft'
            if not self.container_status:
                self.container_status = 'not_created'
            
            # Salva o documento imediatamente para garantir que apareça na lista
            self.flags.ignore_validate = True
            self.flags.ignore_links = True
            self.flags.ignore_mandatory = True  # Ignora campos obrigatórios temporariamente se necessário
            self.save(ignore_permissions=True)
            frappe.db.commit()
            
            frappe.log_error(f"Tenant {self.name} salvo no banco com sucesso (state: {self.state})", "Tenant Created")
            
            # Processa a criação do container de forma ASSÍNCRONA para não travar a interface
            # Isso evita timeout e tela branca
            try:
                # Usa job_name completo para garantir que o worker encontre o módulo
                frappe.enqueue(
                    method='innexar_core.saas_management.doctype.saas_tenant.saas_tenant.create_tenant_container',
                    queue='long',
                    timeout=600,  # 10 minutos de timeout
                    is_async=True,
                    job_name=f'create_tenant_container_{self.name}',
                    tenant_name=self.name
                )
                frappe.msgprint(
                    f"Tenant '{self.tenant_name or self.name}' criado! O container está sendo provisionado em background. Você receberá uma notificação quando estiver pronto.",
                    indicator='blue'
                )
            except Exception as e:
                # Se falhar ao enfileirar, loga mas não bloqueia
                frappe.log_error(f"Erro ao enfileirar criação de container para tenant {self.name}: {str(e)}", "Tenant Queue Error")
                frappe.msgprint(
                    f"Tenant '{self.tenant_name or self.name}' criado! Mas houve um erro ao iniciar o provisionamento. O tenant está em estado 'draft'. Você pode tentar criar o container manualmente.",
                    indicator='orange'
                )
        except Exception as save_error:
            # Se falhar ao salvar, loga o erro mas não bloqueia
            frappe.log_error(f"Erro ao salvar tenant após criação: {str(save_error)}", "Tenant Save Error")
            frappe.msgprint(
                f"Aviso: Tenant pode não ter sido salvo corretamente. Verifique os logs.",
                indicator='red'
            )
    
    def on_trash(self):
        # Remove o container se existir
        try:
            if self.container_name:
                self.delete_container()
            elif self.container_id:
                # Tenta encontrar pelo ID
                try:
                    import docker
                    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
                    container = client.containers.get(self.container_id)
                    container.stop()
                    container.remove(force=True)
                    frappe.log_error(f"Container {self.container_id} removido", "Docker Cleanup")
                except:
                    pass
        except Exception as e:
            frappe.log_error(f"Erro ao remover container: {str(e)}", "Docker Error")
            # Não impede a exclusão do tenant mesmo se falhar ao remover container
    
    def generate_password(self, length=12):
        """Gera uma senha aleatória"""
        chars = string.ascii_letters + string.digits + '!@#$%^&*()'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _get_docker_network(self, client):
        """Descobre a rede Docker do container atual ou cria/usa a padrão."""
        try:
            # Tenta descobrir a rede do container backend atual
            hostname = os.environ.get('HOSTNAME', '')
            if hostname:
                try:
                    current_container = client.containers.get(hostname)
                    networks = current_container.attrs.get('NetworkSettings', {}).get('Networks', {})
                    if networks:
                        # Retorna a primeira rede encontrada
                        return list(networks.keys())[0]
                except:
                    pass
            
            # Tenta encontrar rede com "innexar" no nome
            networks = client.networks.list()
            for net in networks:
                if 'innexar' in net.name.lower():
                    return net.name
            
            # Fallback: tenta criar ou usar rede padrão
            try:
                return client.networks.get('innexar-network').name
            except:
                # Cria a rede se não existir
                net = client.networks.create('innexar-network', driver='bridge')
                return net.name
        except Exception:
            # Último fallback
            return 'innexar-network'
    
    def create_container(self):
        """Cria um container Docker dedicado para o tenant e provisiona o site."""
        try:
            frappe.log_error(f"=== INICIANDO CRIAÇÃO DE CONTAINER PARA TENANT {self.name} ===", "Container Creation")
            
            # Tenta conectar ao Docker usando variável de ambiente ou socket padrão
            docker_host = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
            frappe.log_error(f"Conectando ao Docker em {docker_host}...", "Docker Info")
            client = docker.DockerClient(base_url=docker_host)
            # Testa conexão
            client.ping()
            frappe.log_error("Conexão com Docker estabelecida com sucesso", "Docker Success")
            
            # Descobre a rede correta
            network_name = self._get_docker_network(client)
            
            plan = frappe.get_doc("SAAS Plan", self.plan)
            site = self._build_site_fqdn()
            db_name = f"tenant_{self.subdomain}"
            admin_password = self.admin_password or DEFAULT_ADMIN_PASSWORD

            # escolher porta disponível (verificando Docker e banco)
            port = self.get_available_port(client=client)

            env_vars = {
                'FRAPPE_SITE': site,
                'SITE_NAME': site,
                'ADMIN_PASSWORD': admin_password,
                'DB_HOST': 'db',
                'DB_PORT': '3306',
                'DB_ROOT_USER': 'root',
                'MYSQL_ROOT_PASSWORD': MYSQL_ROOT_PASSWORD,
                'DB_NAME': db_name,
                # Redis configurado para usar os mesmos serviços do backend principal
                'REDIS_CACHE': 'redis-cache:6379',
                'REDIS_QUEUE': 'redis-queue:6379',
                'REDIS_SOCKETIO': 'redis-socketio:6379',
                'SOCKETIO_PORT': '9000',
            }

            # Usar o subdomínio do cliente como nome do container
            container_name = self.subdomain
            
            # Verifica se container já existe e remove se necessário
            try:
                existing = client.containers.get(container_name)
                if existing:
                    frappe.log_error(f"Container {container_name} já existe. Removendo...", "Docker Cleanup")
                    existing.stop()
                    existing.remove(force=True)
            except docker.errors.NotFound:
                # Container não existe, tudo bem
                pass
            except Exception as e:
                frappe.log_error(f"Erro ao verificar/remover container existente: {str(e)}", "Docker Warning")
            
            # Verifica se a imagem existe antes de criar o container
            frappe.log_error(f"Verificando se a imagem {CORE_IMAGE_NAME} existe...", "Docker Info")
            try:
                client.images.get(CORE_IMAGE_NAME)
                frappe.log_error(f"Imagem {CORE_IMAGE_NAME} encontrada", "Docker Success")
            except docker.errors.ImageNotFound:
                frappe.log_error(f"ERRO: Imagem {CORE_IMAGE_NAME} não encontrada! Buildando...", "Docker Error")
                raise Exception(f"Imagem {CORE_IMAGE_NAME} não encontrada. Execute o build da imagem tenant primeiro.")
            
            # Cria o container SEM iniciar (create em vez de run) - innexar_core já está na imagem
            container_created = False
            container_obj = None
            frappe.log_error(f"Criando container {container_name} com imagem {CORE_IMAGE_NAME}...", "Docker Info")
            try:
                # Cria o container sem iniciar
                container_obj = client.containers.create(
                    image=CORE_IMAGE_NAME,
                    name=container_name,
                    ports={'8000/tcp': port},
                    environment=env_vars,
                    restart_policy={"Name": "always"},
                    network=network_name,
                )
                container_created = True
                frappe.log_error(f"Container {container_name} criado (sem iniciar) com sucesso. ID: {container_obj.id}", "Docker Success")
            except Exception as run_error:
                # Se falhar na criação, verifica se foi criado mesmo assim
                error_str = str(run_error)
                frappe.log_error(f"ERRO ao criar container {container_name}: {error_str}", "Docker Error")
                
                is_known_error = (
                    "'NoneType' object has no attribute 'decode'" in error_str or
                    "falha na comunicação" in error_str.lower() or
                    "communication error" in error_str.lower() or
                    "connection aborted" in error_str.lower()
                )
                
                if is_known_error:
                    # Erro conhecido do Docker SDK - container pode ter sido criado mesmo assim
                    frappe.log_error(f"Docker SDK communication error (verificando se container foi criado): {error_str}", "Docker Info")
                else:
                    # Outro erro - verifica se container foi criado mesmo assim
                    frappe.log_error(f"Erro desconhecido ao criar container (verificando se foi criado): {error_str}", "Docker Warning")
                
                # SEMPRE tenta verificar se o container foi criado mesmo com erro
                try:
                    check_container = client.containers.get(container_name)
                    if check_container:
                        frappe.log_error(f"Container {container_name} foi criado mesmo com erro de comunicação!", "Docker Success")
                        container_created = True
                        container_obj = check_container
                except docker.errors.NotFound:
                    frappe.log_error(f"Container {container_name} realmente não foi criado", "Docker Error")
                    raise Exception(f"Falha ao criar container {container_name}: {error_str}")
                except Exception as check_error:
                    frappe.log_error(f"Erro ao verificar container: {str(check_error)}", "Docker Warning")
                    raise Exception(f"Falha ao criar container {container_name}: {error_str}")
            
            # Aguarda um momento e busca o container criado
            if not container_obj:
                time.sleep(1)
                # Tenta buscar o container pelo nome
                try:
                    container_obj = client.containers.get(container_name)
                    frappe.log_error(f"Container {container_name} encontrado pelo nome após criação", "Docker Success")
                except docker.errors.NotFound:
                    # Tenta buscar todos os containers para debug
                    all_containers = client.containers.list(all=True)
                    container_names = [c.name for c in all_containers]
                    frappe.log_error(f"Container {container_name} não encontrado. Containers existentes: {container_names[:10]}", "Docker Error")
                    raise Exception(f"Container {container_name} não foi encontrado após criação. Containers: {', '.join(container_names[:5])}")
            
            # Usa o container encontrado/criado
            container = container_obj
            container.reload()
            frappe.log_error(f"Container {container_name} recuperado (status: {container.status}, ID: {container.id})", "Docker Info")
            
            # innexar_core já está na imagem base (Dockerfile.tenant), não precisa copiar
            frappe.log_error("Container criado com imagem que inclui innexar_core nativamente", "Docker Info")
            
            # Agora inicia o container para que o entrypoint execute
            if container.status != 'running':
                frappe.log_error(f"Iniciando container {container_name}...", "Docker Info")
                container.start()
            
            # Aguarda o container iniciar completamente
            frappe.log_error("Aguardando container iniciar completamente...", "Docker Info")
            max_wait = 120  # 2 minutos para o entrypoint terminar
            container_ready = False
            for i in range(max_wait):
                try:
                    container.reload()
                    if container.status == 'running':
                        # Tenta executar um comando simples para verificar se está pronto
                        try:
                            result = container.exec_run("echo 'ready'", user='frappe', timeout=5)
                            if result.exit_code == 0:
                                container_ready = True
                                frappe.log_error(f"Container pronto após {i+1} segundos", "Docker Info")
                                break
                        except:
                            pass  # Ainda não está pronto
                    time.sleep(2)
                except Exception as e:
                    if i % 10 == 0:  # Log a cada 10 tentativas
                        frappe.log_error(f"Aguardando container ficar pronto... tentativa {i+1}/{max_wait}", "Docker Info")
                    time.sleep(2)
            
            if not container_ready:
                frappe.log_error("Aviso: Container pode não estar completamente pronto, mas continuando...", "Docker Warning")
            
            # Aguarda mais um pouco para garantir que o entrypoint terminou
            frappe.log_error("Aguardando entrypoint terminar de executar...", "Docker Info")
            time.sleep(10)
            
            # Garante que está rodando
            try:
                container.reload()
                if container.status != 'running':
                    # Tenta obter logs para debug
                    try:
                        logs = container.logs(tail=50).decode('utf-8')
                        frappe.log_error(f"Container não está rodando. Logs: {logs}", "Docker Error")
                    except:
                        pass
                    raise Exception(f"Container {container_name} não está rodando (status: {container.status})")
            except docker.errors.APIError as e:
                frappe.log_error(f"Erro da API Docker: {str(e)}", "Docker Error")
                raise Exception(f"Erro ao verificar container: {str(e)}")

            # Verifica e instala innexar_core no site (já está na imagem base, só precisa instalar no site)
            frappe.log_error("Verificando instalação do innexar_core no site...", "Docker Info")
            try:
                site_name = self._build_site_fqdn()
                
                # Verifica se innexar_core está instalado no site
                check_site = container.exec_run(
                    f"bash -c 'cd /home/frappe/bench-repo && . env/bin/activate && bench --site {site_name} list-apps | grep innexar_core && echo \"INSTALLED\"'",
                    user='frappe',
                    timeout=30
                )
                
                if check_site.exit_code != 0:
                    # Não está instalado no site - instala agora
                    frappe.log_error(f"innexar_core não está instalado no site {site_name}, instalando...", "Docker Info")
                    install_site = container.exec_run(
                        f"bash -c 'cd /home/frappe/bench-repo && . env/bin/activate && bench --site {site_name} install-app innexar_core'",
                        user='frappe',
                        timeout=300
                    )
                    if install_site.exit_code != 0:
                        error_output = install_site.output.decode() if hasattr(install_site.output, 'decode') else str(install_site.output)
                        frappe.log_error(f"Erro ao instalar innexar_core no site: {error_output}", "Docker Error")
                        # Tenta novamente uma vez
                        frappe.log_error("Tentando instalar novamente...", "Docker Warning")
                        time.sleep(5)
                        install_site_retry = container.exec_run(
                            f"bash -c 'cd /home/frappe/bench-repo && . env/bin/activate && bench --site {site_name} install-app innexar_core'",
                            user='frappe',
                            timeout=300
                        )
                        if install_site_retry.exit_code != 0:
                            error_output_retry = install_site_retry.output.decode() if hasattr(install_site_retry.output, 'decode') else str(install_site_retry.output)
                            frappe.log_error(f"Erro na segunda tentativa: {error_output_retry}", "Docker Error")
                            raise Exception(f"Falha ao instalar innexar_core no site após 2 tentativas: {error_output_retry}")
                        else:
                            frappe.log_error(f"innexar_core instalado no site {site_name} na segunda tentativa", "Docker Success")
                    else:
                        frappe.log_error(f"innexar_core instalado no site {site_name} com sucesso", "Docker Success")
                else:
                    frappe.log_error(f"innexar_core já está instalado no site {site_name}", "Docker Info")
                
            except Exception as e:
                error_msg = str(e)
                frappe.log_error(f"Erro ao verificar/instalar innexar_core no site: {error_msg}", "Docker Error")
                # Não falha a criação do tenant, mas loga o erro
                frappe.log_error(f"Tenant criado mas innexar_core pode não estar instalado no site", "Docker Warning")
            
            # pós-setup: aplicar apps adicionais e brand/idiomas via backend compartilhado
            self._apply_plan_apps(site)
            self._apply_brand_and_languages(site)

            # Atualiza status
            # GARANTE que container_name seja sempre o subdomain (não pode ser "backend" ou outro)
            self.container_id = container.id
            self.container_name = self.subdomain  # SEMPRE usa subdomain como nome do container
            self.container_port = port
            self.container_status = 'running'
            self.state = 'active'
            self.access_url = f"http://{site}"
            
            # Salva o documento (usando save com ignore_permissions para evitar problemas)
            self.flags.ignore_validate = True
            self.flags.ignore_links = True
            self.save(ignore_permissions=True)
            frappe.db.commit()
            
            # Recarrega o documento para garantir que o frontend receba os dados atualizados
            frappe.clear_cache(doctype=self.doctype)
            self.reload()

            frappe.msgprint(f"Container criado e site provisionado: {container_name} -> {site}")
            return True
        except docker.errors.APIError as e:
            # Erro de API do Docker (409 Conflict, 500 port already allocated, etc)
            error_msg = str(e)
            if "409" in error_msg or "Conflict" in error_msg or "already in use" in error_msg:
                if "name" in error_msg.lower():
                    message = "Container já existe. Tente novamente ou remova manualmente"
                else:
                    message = "Recurso já em uso. Tente novamente"
            elif "500" in error_msg and ("port" in error_msg.lower() or "already allocated" in error_msg.lower()):
                message = "Porta já em uso. Tente novamente (porta será reatribuída)"
            elif "Permission denied" in error_msg or "permission" in error_msg.lower():
                message = "Erro de permissão Docker. Verifique docker.sock"
            else:
                message = f"Erro Docker: {error_msg}"
            short = (message[:137] + '...') if len(message) > 140 else message
            frappe.log_error(f"Erro ao criar container do tenant: {error_msg}", "Docker Error")
            frappe.throw(short)
        except docker.errors.DockerException as e:
            # Erro específico do Docker (permissão, conexão, etc)
            error_msg = str(e)
            if "Permission denied" in error_msg or "permission" in error_msg.lower():
                message = "Erro de permissão Docker. Verifique docker.sock"
            else:
                message = f"Erro Docker: {error_msg}"
            short = (message[:137] + '...') if len(message) > 140 else message
            frappe.log_error(f"Erro ao criar container do tenant: {error_msg}", "Docker Error")
            frappe.throw(short)
        except AttributeError as e:
            # Erro comum do Docker SDK com NoneType - não lança exceção, verifica se container foi criado
            error_msg = str(e)
            if "'NoneType' object has no attribute 'decode'" in error_msg or "falha na comunicação" in error_msg.lower():
                # Erro conhecido do Docker SDK - verifica se container foi criado
                frappe.log_error(f"Docker SDK communication error (verificando se container foi criado): {error_msg}", "Docker Info")
                
                # Tenta recuperar o container
                try:
                    container = client.containers.get(container_name)
                    container.reload()
                    frappe.log_error(f"Container {container_name} recuperado após erro de comunicação do Docker SDK", "Docker Success")
                    
                    # Continua o processo normalmente
                    self._install_innexar_core(container)
                    self._apply_plan_apps(site)
                    self._apply_brand_and_languages(site)
                    
                    self.container_id = container.id
                    self.container_name = self.subdomain  # SEMPRE usa subdomain
                    self.container_port = port
                    self.container_status = 'running'
                    self.state = 'active'
                    self.access_url = f"http://{site}"
                    
                    self.flags.ignore_validate = True
                    self.flags.ignore_links = True
                    self.save(ignore_permissions=True)
                    frappe.db.commit()
                    
                    # Recarrega o documento para garantir que o frontend receba os dados atualizados
                    frappe.clear_cache(doctype=self.doctype)
                    self.reload()
                    
                    frappe.msgprint(f"Container criado e site provisionado: {container_name} -> {site}", indicator='green')
                    return True
                except docker.errors.NotFound:
                    # Container realmente não foi criado
                    frappe.log_error(f"Container {container_name} não foi criado", "Docker Error")
                    raise Exception("Erro Docker SDK: falha na comunicação. Container não foi criado.")
                except Exception as recovery_error:
                    frappe.log_error(f"Erro ao recuperar container após erro de comunicação: {str(recovery_error)}", "Docker Error")
                    raise Exception(f"Erro ao criar container: {str(recovery_error)}")
            else:
                message = f"Erro de atributo: {error_msg}"
                short = (message[:137] + '...') if len(message) > 140 else message
                frappe.log_error(f"Erro ao criar container do tenant: {error_msg}", "Docker SDK Error")
                frappe.throw(short)
        except Exception as e:
            # Verifica se é erro de comunicação antes de lançar exceção
            error_msg = str(e)
            is_communication_error = (
                "falha na comunicação" in error_msg.lower() or
                "communication error" in error_msg.lower() or
                "connection aborted" in error_msg.lower() or
                "erro ao recuperar container" in error_msg.lower()
            )
            
            if is_communication_error:
                # Tenta recuperar o container uma última vez
                try:
                    container = client.containers.get(container_name)
                    container.reload()
                    frappe.log_error(f"Container {container_name} recuperado após Exception de comunicação", "Docker Success")
                    
                    # Continua o processo normalmente
                    self._install_innexar_core(container)
                    self._apply_plan_apps(site)
                    self._apply_brand_and_languages(site)
                    
                    self.container_id = container.id
                    self.container_name = self.subdomain  # SEMPRE usa subdomain
                    self.container_port = port
                    self.container_status = 'running'
                    self.state = 'active'
                    self.access_url = f"http://{site}"
                    
                    self.flags.ignore_validate = True
                    self.flags.ignore_links = True
                    self.save(ignore_permissions=True)
                    frappe.db.commit()
                    
                    # Recarrega o documento para garantir que o frontend receba os dados atualizados
                    frappe.clear_cache(doctype=self.doctype)
                    self.reload()
                    
                    frappe.msgprint(f"Container criado e site provisionado: {container_name} -> {site}", indicator='green')
                    return True
                except docker.errors.NotFound:
                    # Container não existe - lança exceção
                    frappe.log_error(f"Container {container_name} não encontrado após Exception de comunicação", "Docker Error")
                    message = "Erro Docker SDK: falha na comunicação. Container não foi criado."
                    short = (message[:137] + '...') if len(message) > 140 else message
                    frappe.throw(short)
                except Exception as recovery_error:
                    # Outro erro ao recuperar
                    frappe.log_error(f"Erro ao recuperar container após Exception: {str(recovery_error)}", "Docker Error")
                    message = f"Erro ao criar container: {str(recovery_error)}"
                    short = (message[:137] + '...') if len(message) > 140 else message
                    frappe.throw(short)
            
            # Não é erro de comunicação - trata normalmente
            message = f"Erro ao criar container do tenant: {error_msg}"
            short = (message[:137] + '...') if len(message) > 140 else message
            frappe.log_error(message)
            frappe.throw(short)

    def _build_site_fqdn(self) -> str:
        base_domain = frappe.local.conf.get('base_domain', 'innexar.local')
        return f"{self.subdomain}.{base_domain}"

    def _bench_new_site(self, site: str, db_name: str, admin_password: str):
        bench_new_site(
            site=site,
            mariadb_root_password=MYSQL_ROOT_PASSWORD,
            admin_password=admin_password,
            db_name=db_name,
        )

    def _bench_install_app(self, site: str, app: str):
        bench_install_app(site=site, app=app)

    def _apply_plan_apps(self, site: str):
        """Instala apps adicionais conforme o plano (placeholder para futuras apps)."""
        try:
            plan = frappe.get_doc("SAAS Plan", self.plan)
            # Exemplo: se enterprise, instalar 'payments' caso exista
            plan_name = (plan.technical_name or plan.name or '').lower()
            if 'enterprise' in plan_name:
                try:
                    self._bench_install_app(site=site, app="payments")
                except Exception:
                    pass
        except Exception:
            # Não bloquear provisionamento por falha opcional
            pass

    def _install_innexar_core(self, container, start_container=True):
        """Instala o innexar_core no container do tenant
        
        Args:
            container: Container Docker
            start_container: Se True, aguarda container estar rodando. Se False, trabalha com container parado.
        """
        try:
            frappe.log_error(f"Iniciando instalação do innexar_core no container {container.name} (start_container={start_container})", "Docker Info")
            
            # Se start_container=True, aguarda container estar rodando
            if start_container:
                # Aguardar o container estar pronto para receber comandos
                frappe.log_error("Aguardando container ficar pronto...", "Docker Info")
                max_wait = 60  # Aumentado para 60 segundos
                for i in range(max_wait):
                    try:
                        result = container.exec_run("echo 'Container ready'", user='frappe')
                        if result.exit_code == 0:
                            frappe.log_error(f"Container pronto após {i+1} segundos", "Docker Info")
                            break
                    except Exception as e:
                        if i % 10 == 0:  # Log a cada 10 tentativas
                            frappe.log_error(f"Aguardando container... tentativa {i+1}/{max_wait}", "Docker Info")
                    time.sleep(1)
                    if i == max_wait - 1:
                        raise Exception("Container não ficou pronto a tempo")
                
                # Aguardar mais um pouco para garantir que o sistema de arquivos está pronto
                time.sleep(5)
            else:
                # Container está parado - apenas aguarda um momento para garantir que está criado
                time.sleep(2)
            
            # Copiar innexar_core do container backend para o tenant
            # Como estamos rodando dentro do container backend, o innexar_core já está instalado aqui
            import subprocess
            import os
            import shutil
            
            frappe.log_error(f"Copiando innexar_core do container backend para {container.name}", "Docker Info")
            
            # Primeira tentativa: copiar do container backend (onde estamos rodando)
            docker_cmd = shutil.which('docker')
            if not docker_cmd:
                # Se docker não estiver no PATH, tenta caminhos comuns
                docker_cmd = '/usr/bin/docker'
                if not os.path.exists(docker_cmd):
                    docker_cmd = 'docker'  # Tenta do PATH de qualquer forma
            
            try:
                # Tenta copiar do backend para o tenant (funciona mesmo com container parado)
                copy_from_backend = subprocess.run([
                    docker_cmd, 'cp',
                    'innexar-backend:/home/frappe/bench-repo/apps/innexar_core',
                    f'{container.name}:/home/frappe/bench-repo/apps/innexar_core'
                ], capture_output=True, text=True, timeout=300)
                
                if copy_from_backend.returncode != 0:
                    error_msg = copy_from_backend.stderr or copy_from_backend.stdout
                    frappe.log_error(f"Falha ao copiar do backend: {error_msg}", "Docker Warning")
                    raise Exception(f"Falha ao copiar innexar_core do backend: {error_msg}")
                
                frappe.log_error(f"innexar_core copiado do backend com sucesso", "Docker Success")
            except Exception as copy_error:
                # Se falhar, tenta copiar do host (se montado)
                frappe.log_error(f"Tentando copiar do host como fallback...", "Docker Info")
                # O caminho dentro do container backend onde o innexar_core está instalado
                innexar_core_path = '/home/frappe/bench-repo/apps/innexar_core'
                
                if os.path.exists(innexar_core_path):
                    copy_result = subprocess.run([
                        docker_cmd, 'cp',
                        innexar_core_path,
                        f'{container.name}:/home/frappe/bench-repo/apps/innexar_core'
                    ], capture_output=True, text=True, timeout=300)
                    
                    if copy_result.returncode != 0:
                        error_msg = copy_result.stderr or copy_result.stdout
                        raise Exception(f"Falha ao copiar innexar_core: {error_msg}")
                else:
                    raise Exception(f"innexar_core não encontrado em {innexar_core_path} e cópia do backend falhou: {str(copy_error)}")
            
            frappe.log_error(f"innexar_core copiado com sucesso", "Docker Success")
            
            # Se o container está rodando, ajusta permissões e instala
            if start_container:
                # Ajustar permissões (como root primeiro)
                frappe.log_error("Ajustando permissões...", "Docker Info")
                perm_result = container.exec_run('chown -R frappe:frappe /home/frappe/bench-repo/apps/innexar_core', user='root')
                if perm_result.exit_code != 0:
                    frappe.log_error(f"Aviso: Erro ao ajustar permissões: {perm_result.output.decode() if hasattr(perm_result.output, 'decode') else perm_result.output}", "Docker Warning")
                
                # Verificar se foi copiado corretamente
                check_result = container.exec_run('test -d /home/frappe/bench-repo/apps/innexar_core && echo "OK"', user='frappe')
                if check_result.exit_code != 0:
                    raise Exception("innexar_core não foi copiado corretamente")
                
                # Garantir que apps.txt está correto
                frappe.log_error("Atualizando apps.txt...", "Docker Info")
                apps_result = container.exec_run(
                    "bash -c 'echo -e \"frappe\\nerpnext\\ninnexar_core\" > /home/frappe/bench-repo/sites/apps.txt'",
                    user='frappe'
                )
                
                if apps_result.exit_code != 0:
                    error_output = apps_result.output.decode() if hasattr(apps_result.output, 'decode') else str(apps_result.output)
                    frappe.log_error(f"Erro ao atualizar apps.txt: {error_output}", "Docker Warning")
                
                # Instalar o app no ambiente virtual
                frappe.log_error("Instalando innexar_core no ambiente virtual...", "Docker Info")
                
                install_cmd = "bash -c 'cd /home/frappe/bench-repo && . env/bin/activate && cd apps/innexar_core && pip install -e .'"
                install_result = container.exec_run(install_cmd, user='frappe', timeout=300)
                
                if install_result.exit_code != 0:
                    error_output = install_result.output.decode() if hasattr(install_result.output, 'decode') else str(install_result.output)
                    frappe.log_error(f"Erro ao instalar innexar_core: {error_output}", "Docker Error")
                    raise Exception(f"Falha ao instalar innexar_core: {error_output}")
                else:
                    frappe.log_error(f"innexar_core instalado com sucesso no container {container.name}", "Docker Success")
                
                # Instalar o app no site (se o site já existir)
                try:
                    site_name = self._build_site_fqdn()
                    frappe.log_error(f"Instalando innexar_core no site {site_name}...", "Docker Info")
                    install_site_result = container.exec_run(
                        f"bash -c 'cd /home/frappe/bench-repo && . env/bin/activate && bench --site {site_name} install-app innexar_core'",
                        user='frappe',
                        timeout=300
                    )
                    if install_site_result.exit_code == 0:
                        frappe.log_error(f"innexar_core instalado no site {site_name} com sucesso", "Docker Success")
                    else:
                        error_output = install_site_result.output.decode() if hasattr(install_site_result.output, 'decode') else str(install_site_result.output)
                        frappe.log_error(f"Aviso: Erro ao instalar innexar_core no site: {error_output}", "Docker Warning")
                except Exception as site_error:
                    frappe.log_error(f"Aviso: Não foi possível instalar innexar_core no site: {str(site_error)}", "Docker Warning")
            else:
                # Container está parado - apenas copiamos os arquivos
                # A instalação será feita pelo entrypoint quando o container iniciar
                frappe.log_error("Container parado - arquivos copiados. Instalação será feita pelo entrypoint ao iniciar", "Docker Info")
            
            # Reiniciar o processo do Frappe para carregar o novo app (apenas se container estiver rodando)
            if start_container:
                frappe.log_error("Reiniciando processos do Frappe...", "Docker Info")
                try:
                    container.exec_run("supervisorctl restart all", user='root', timeout=30)
                    time.sleep(5)
                except:
                    # Se não tiver supervisorctl, tenta reiniciar manualmente
                    frappe.log_error("Aviso: Não foi possível reiniciar via supervisorctl", "Docker Warning")
            else:
                frappe.log_error("Container não iniciado ainda - processos serão iniciados quando container iniciar", "Docker Info")
            
            frappe.log_error(f"Instalação do innexar_core concluída no container {container.name}", "Docker Success")
            
        except Exception as e:
            error_msg = str(e)
            frappe.log_error(f"Erro ao instalar innexar_core no container {container.name}: {error_msg}", "Docker Error")
            # Re-raise para que o código que chama possa tratar
            raise
    
    def _apply_brand_and_languages(self, site: str):
        languages = ["en", "pt-BR", "es-ES"]
        default_language = "pt-BR"
        app_name = "Innexar ERP Cloud"
        # bench execute <module.path>:func --args '{"languages":[...],"default_language":"pt-BR","app_name":"..."}'
        args_json = json.dumps({
            "languages": languages,
            "default_language": default_language,
            "app_name": app_name,
        })
        cmd = (
            f"bench --site {site} execute "
            f"innexar_core.saas_management.utils.site_post_setup.apply_brand_and_languages "
            f"--kwargs '{args_json}'"
        )
        run_bench(cmd)
    
    def get_available_port(self, client=None):
        """Encontra uma porta disponível para o container, verificando Docker e banco"""
        # Porta 8000 é reservada para o backend principal
        reserved_ports = {8000, 9000}
        
        # Portas usadas no banco de dados
        used_ports = frappe.get_all("SAAS Tenant", 
                                 filters={"container_port": ["!=", ""], "name": ["!=", self.name]}, 
                                 fields=["container_port"])
        used_ports = {int(p['container_port']) for p in used_ports if p['container_port']}
        used_ports.update(reserved_ports)
        
        # Se temos cliente Docker, verifica portas realmente em uso
        if client:
            try:
                containers = client.containers.list(all=True)
                for container in containers:
                    try:
                        # Verifica portas mapeadas no container
                        ports = container.attrs.get('HostConfig', {}).get('PortBindings', {})
                        if ports:
                            for port_bindings in ports.values():
                                if isinstance(port_bindings, list):
                                    for binding in port_bindings:
                                        if isinstance(binding, dict):
                                            host_port = binding.get('HostPort')
                                            if host_port:
                                                used_ports.add(int(host_port))
                    except Exception:
                        # Ignora erros de container individual
                        continue
            except Exception:
                # Se falhar, continua só com verificação do banco
                pass
        
        # Tenta portas de 8001 a 8999 (evitando 8000 e 9000)
        for port in range(8001, 9000):
            if port not in used_ports:
                return port
        
        frappe.throw("Não há portas disponíveis para criar um novo container.")
    
    def start_container(self):
        """Compat: método mantido; não usado no modelo sem container por tenant."""
        frappe.msgprint("Operação não necessária: tenant roda no backend compartilhado.")
    
    def stop_container(self):
        """Compat: método mantido; não usado no modelo sem container por tenant."""
        self.state = 'suspended'
        self.container_status = 'stopped'
        self.save()
        frappe.msgprint("Tenant marcado como suspenso.")
    
    def sync_container_info(self):
        """Sincroniza informações do container com o Docker"""
        try:
            import docker
            client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            
            # Tenta encontrar o container pelo subdomínio (nome correto)
            container_name = self.subdomain
            try:
                container = client.containers.get(container_name)
                container.reload()
                
                # Atualiza informações
                self.container_id = container.id
                self.container_name = self.subdomain  # SEMPRE usa subdomain
                self.container_status = 'running' if container.status == 'running' else 'stopped'
                self.state = 'active' if container.status == 'running' else 'draft'
                
                # Tenta obter a porta
                ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                if '8000/tcp' in ports and ports['8000/tcp']:
                    self.container_port = ports['8000/tcp'][0]['HostPort']
                
                self.flags.ignore_validate = True
                self.save(ignore_permissions=True)
                frappe.db.commit()
                
                frappe.msgprint(f"Informações do container sincronizadas! Nome: {container_name}", indicator='green')
                return True
            except docker.errors.NotFound:
                frappe.msgprint(f"Container {container_name} não encontrado no Docker", indicator='orange')
                return False
        except Exception as e:
            frappe.log_error(f"Erro ao sincronizar container: {str(e)}", "Docker Sync Error")
            frappe.msgprint(f"Erro ao sincronizar: {str(e)}", indicator='red')
            return False
    
    def delete_container(self):
        """Remove o container Docker do tenant"""
        try:
            import docker
            client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            
            # Tenta encontrar o container pelo nome (subdomínio)
            container_name = self.container_name or self.subdomain
            
            try:
                container = client.containers.get(container_name)
                
                # Para e remove o container
                if container.status == 'running':
                    container.stop()
                container.remove(force=True)
                
                frappe.log_error(f"Container {container_name} removido com sucesso", "Docker Cleanup")
                frappe.msgprint(f"Container {container_name} removido com sucesso", indicator='green')
            except docker.errors.NotFound:
                frappe.log_error(f"Container {container_name} não encontrado (já foi removido?)", "Docker Info")
                frappe.msgprint(f"Container {container_name} não encontrado", indicator='orange')
            except Exception as e:
                frappe.log_error(f"Erro ao remover container {container_name}: {str(e)}", "Docker Error")
                frappe.msgprint(f"Erro ao remover container: {str(e)}", indicator='red')
            
            # Limpa os campos mesmo se o container não foi encontrado
            self.container_id = None
            self.container_name = None
            self.container_port = None
            self.container_status = 'not_created'
            self.state = 'draft'
            self.save()
            
        except Exception as e:
            frappe.log_error(f"Erro ao deletar container: {str(e)}", "Docker Error")
            # Limpa os campos mesmo com erro
            self.container_id = None
            self.container_name = None
            self.container_port = None
            self.container_status = 'not_created'
            self.state = 'draft'
            self.save()
            frappe.msgprint(f"Erro ao remover container, mas campos foram limpos: {str(e)}", indicator='orange')

@frappe.whitelist()
def create_tenant_container(tenant_name):
    """Função para criar container do tenant de forma assíncrona"""
    try:
        frappe.log_error(f"Iniciando criação de container para tenant: {tenant_name}", "Tenant Container Start")
        
        # Tenta buscar o tenant por nome ou tenant_name
        tenant = None
        try:
            tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        except frappe.DoesNotExistError:
            # Tenta buscar por tenant_name
            tenants = frappe.get_all("SAAS Tenant", filters={"tenant_name": tenant_name}, limit=1)
            if tenants:
                tenant = frappe.get_doc("SAAS Tenant", tenants[0].name)
            else:
                # Tenta buscar por subdomain
                tenants = frappe.get_all("SAAS Tenant", filters={"subdomain": tenant_name}, limit=1)
                if tenants:
                    tenant = frappe.get_doc("SAAS Tenant", tenants[0].name)
        
        if not tenant:
            raise Exception(f"Tenant '{tenant_name}' não encontrado no banco de dados")
        
        frappe.log_error(f"Tenant encontrado: {tenant.name} (tenant_name: {tenant.tenant_name}, subdomain: {tenant.subdomain})", "Tenant Found")
        
        # Atualiza status para provisioning
        tenant.state = 'provisioning'
        tenant.container_status = 'provisioning'
        tenant.flags.ignore_validate = True
        tenant.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.log_error(f"Tenant {tenant.name} atualizado para estado 'provisioning'", "Tenant Status Updated")
        
        # Cria o container
        frappe.log_error(f"Iniciando criação do container para tenant {tenant.name}...", "Container Creation Start")
        try:
            result = tenant.create_container()
            if result:
                frappe.log_error(f"Container criado com sucesso para tenant {tenant.name}", "Container Created")
            else:
                frappe.log_error(f"create_container retornou False para tenant {tenant.name}", "Container Creation Warning")
                raise Exception("create_container retornou False")
        except Exception as create_error:
            error_str = str(create_error)
            frappe.log_error(f"Erro ao chamar create_container para tenant {tenant.name}: {error_str}", "Container Creation Error")
            # Recarrega o tenant para verificar status atual
            tenant.reload()
            frappe.log_error(f"Status do tenant após erro: state={tenant.state}, container_status={tenant.container_status}", "Tenant Status After Error")
            raise  # Re-lança a exceção para ser tratada pelo except externo
        
        # Notifica sucesso
        frappe.publish_realtime('tenant_created', {
            'tenant_name': tenant.name,
            'status': 'success',
            'message': 'Container criado com sucesso!'
        }, user=frappe.session.user)
        
        frappe.log_error(f"Notificação de sucesso enviada para tenant {tenant.name}", "Success Notification")
        
    except Exception as e:
        error_msg = str(e)
        frappe.log_error(f"Erro ao criar container do tenant {tenant_name}: {error_msg}", "Tenant Container Creation Error")
        
        # Tenta buscar o tenant novamente para atualizar o status
        tenant = None
        error_message = error_msg  # Define para usar depois
        try:
            tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        except:
            # Tenta buscar por tenant_name ou subdomain
            try:
                tenants = frappe.get_all("SAAS Tenant", filters={"tenant_name": tenant_name}, limit=1)
                if tenants:
                    tenant = frappe.get_doc("SAAS Tenant", tenants[0].name)
                else:
                    tenants = frappe.get_all("SAAS Tenant", filters={"subdomain": tenant_name}, limit=1)
                    if tenants:
                        tenant = frappe.get_doc("SAAS Tenant", tenants[0].name)
            except:
                pass
        
        if tenant:
            try:
                # Verifica se o container foi criado mesmo com erro
                try:
                    import docker
                    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
                    container_name = tenant.subdomain
                    try:
                        container = client.containers.get(container_name)
                        if container:
                            container.reload()
                            tenant.container_id = container.id
                            tenant.container_name = container_name
                            tenant.container_status = 'running' if container.status == 'running' else 'stopped'
                            tenant.state = 'active' if container.status == 'running' else 'draft'
                            tenant.flags.ignore_validate = True
                            tenant.save(ignore_permissions=True)
                            frappe.db.commit()
                            frappe.publish_realtime('tenant_created', {
                                'tenant_name': tenant_name,
                                'status': 'success',
                                'message': 'Container criado mesmo com erro de comunicação'
                            }, user=frappe.session.user)
                            return
                    except docker.errors.NotFound:
                        pass
                except Exception as docker_error:
                    frappe.log_error(f"Erro ao verificar container: {str(docker_error)}", "Docker Check Error")
                
                # Container não foi criado - mantém como draft
                tenant.state = 'draft'
                tenant.container_status = 'not_created'
                tenant.flags.ignore_validate = True
                tenant.save(ignore_permissions=True)
                frappe.db.commit()
                
            except Exception as save_error:
                frappe.log_error(f"Erro ao salvar estado do tenant após erro: {str(save_error)}", "Tenant Save Error")
        
        # Notifica erro
        try:
            error_message = error_message if 'error_message' in locals() else error_msg if 'error_msg' in locals() else str(e)
        except:
            error_message = "Erro desconhecido ao criar container"
        
        frappe.publish_realtime('tenant_created', {
            'tenant_name': tenant_name,
            'status': 'error',
            'message': error_message[:200]  # Limita tamanho da mensagem
        }, user=frappe.session.user)

@frappe.whitelist()
def sync_container_info(tenant_name):
    """Sincroniza informações do container com o Docker"""
    try:
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        return tenant.sync_container_info()
    except Exception as e:
        frappe.log_error(f"Erro ao sincronizar container do tenant {tenant_name}: {str(e)}", "Docker Sync Error")
        return False

@frappe.whitelist()
def delete_tenant_container(tenant_name):
    """Remove o container Docker do tenant"""
    try:
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        tenant.delete_container()
        return {"status": "success", "message": "Container removido com sucesso"}
    except Exception as e:
        frappe.log_error(f"Erro ao remover container do tenant {tenant_name}: {str(e)}", "Docker Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def restart_tenant_container(tenant_name):
    """Reinicia o container Docker do tenant"""
    try:
        import docker
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        
        container_name = tenant.container_name or tenant.subdomain
        container = client.containers.get(container_name)
        
        container.restart()
        container.reload()
        
        # Atualiza status
        tenant.container_status = 'running' if container.status == 'running' else 'stopped'
        tenant.state = 'active' if container.status == 'running' else tenant.state
        tenant.flags.ignore_validate = True
        tenant.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"status": "success", "message": f"Container {container_name} reiniciado com sucesso"}
    except docker.errors.NotFound:
        return {"status": "error", "message": f"Container {container_name} não encontrado"}
    except Exception as e:
        frappe.log_error(f"Erro ao reiniciar container do tenant {tenant_name}: {str(e)}", "Docker Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def start_tenant_container(tenant_name):
    """Inicia o container Docker do tenant"""
    try:
        import docker
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        
        container_name = tenant.container_name or tenant.subdomain
        container = client.containers.get(container_name)
        
        container.start()
        container.reload()
        
        # Atualiza status
        tenant.container_status = 'running'
        tenant.state = 'active'
        tenant.flags.ignore_validate = True
        tenant.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"status": "success", "message": f"Container {container_name} iniciado com sucesso"}
    except docker.errors.NotFound:
        return {"status": "error", "message": f"Container {container_name} não encontrado"}
    except Exception as e:
        frappe.log_error(f"Erro ao iniciar container do tenant {tenant_name}: {str(e)}", "Docker Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def stop_tenant_container(tenant_name):
    """Para o container Docker do tenant"""
    try:
        import docker
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        
        container_name = tenant.container_name or tenant.subdomain
        container = client.containers.get(container_name)
        
        container.stop()
        container.reload()
        
        # Atualiza status
        tenant.container_status = 'stopped'
        tenant.state = 'suspended'
        tenant.flags.ignore_validate = True
        tenant.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"status": "success", "message": f"Container {container_name} parado com sucesso"}
    except docker.errors.NotFound:
        return {"status": "error", "message": f"Container {container_name} não encontrado"}
    except Exception as e:
        frappe.log_error(f"Erro ao parar container do tenant {tenant_name}: {str(e)}", "Docker Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_tenant(tenant_data):
    """Cria um novo tenant via API"""
    try:
        if isinstance(tenant_data, str):
            tenant_data = json.loads(tenant_data)
        
        # Verifica se o plano existe
        if not frappe.db.exists("SAAS Plan", tenant_data.get("plan")):
            return {"status": "error", "message": "Plano não encontrado"}
        
        # Cria o tenant
        tenant = frappe.new_doc("SAAS Tenant")
        tenant.update(tenant_data)
        tenant.insert(ignore_permissions=True)
        
        return {
            "status": "success", 
            "message": "Tenant criado com sucesso", 
            "name": tenant.name,
            "access_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}",
            "admin_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}/app"
        }
    except Exception as e:
        frappe.log_error(f"Erro ao criar tenant: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def recreate_tenant_container(tenant_name):
    """Reconstrói o container Docker do tenant (remove e cria novamente) de forma assíncrona"""
    try:
        # Enfileira a reconstrução de forma assíncrona
        frappe.enqueue(
            method='innexar_core.saas_management.doctype.saas_tenant.saas_tenant._recreate_tenant_container_async',
            queue='long',
            timeout=600,
            is_async=True,
            job_name=f'recreate_container_{tenant_name}',
            tenant_name=tenant_name
        )
        
        return {
            "status": "success",
            "message": "Reconstrução do container iniciada em background. Você receberá uma notificação quando estiver pronto."
        }
    except Exception as e:
        error_msg = str(e)
        frappe.log_error(f"Erro ao enfileirar reconstrução do container: {error_msg}", "Docker Error")
        return {"status": "error", "message": error_msg}

def _recreate_tenant_container_async(tenant_name):
    """Função assíncrona para reconstruir o container"""
    try:
        import docker
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        
        if not tenant.subdomain:
            frappe.publish_realtime('container_recreate_error', {
                'tenant_name': tenant.name,
                'message': 'Subdomínio não definido'
            }, user=frappe.session.user)
            return
        
        # Garante que container_name seja o subdomain
        container_name = tenant.subdomain
        
        frappe.log_error(f"Iniciando reconstrução do container {container_name} para tenant {tenant_name}", "Docker Recreate")
        
        # Atualiza status para provisioning
        tenant.state = 'provisioning'
        tenant.container_status = 'provisioning'
        tenant.flags.ignore_validate = True
        tenant.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Conecta ao Docker
        docker_host = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
        client = docker.DockerClient(base_url=docker_host)
        
        # Remove container existente se houver (com qualquer nome)
        containers_to_remove = []
        
        # Verifica se existe container com o nome correto (subdomain)
        try:
            correct_container = client.containers.get(container_name)
            containers_to_remove.append(correct_container)
        except docker.errors.NotFound:
            pass
        
        # Verifica se existe container com nome antigo (se estiver diferente)
        if tenant.container_name and tenant.container_name != container_name:
            try:
                old_container = client.containers.get(tenant.container_name)
                containers_to_remove.append(old_container)
            except docker.errors.NotFound:
                pass
        
        # Remove todos os containers encontrados
        for container in containers_to_remove:
            try:
                frappe.log_error(f"Removendo container existente: {container.name}", "Docker Cleanup")
                if container.status == 'running':
                    container.stop(timeout=10)
                container.remove(force=True)
            except Exception as e:
                frappe.log_error(f"Erro ao remover container {container.name}: {str(e)}", "Docker Warning")
        
        # Limpa campos do tenant
        tenant.container_id = None
        tenant.container_name = None
        tenant.container_port = None
        tenant.container_status = 'not_created'
        tenant.state = 'draft'
        tenant.flags.ignore_validate = True
        tenant.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Chama create_container para criar novamente
        frappe.log_error(f"Criando novo container {container_name}...", "Docker Recreate")
        result = tenant.create_container()
        
        if result:
            frappe.log_error(f"Container {container_name} reconstruído com sucesso", "Docker Success")
            frappe.publish_realtime('container_recreated', {
                'tenant_name': tenant.name,
                'container_name': tenant.container_name,
                'container_port': tenant.container_port,
                'access_url': tenant.access_url,
                'message': 'Container reconstruído com sucesso!'
            }, user=frappe.session.user)
        else:
            frappe.publish_realtime('container_recreate_error', {
                'tenant_name': tenant.name,
                'message': 'Falha ao criar container'
            }, user=frappe.session.user)
            
    except Exception as e:
        error_msg = str(e)
        frappe.log_error(f"Erro ao reconstruir container do tenant {tenant_name}: {error_msg}", "Docker Error")
        frappe.publish_realtime('container_recreate_error', {
            'tenant_name': tenant_name,
            'message': error_msg
        }, user=frappe.session.user)

@frappe.whitelist()
def get_tenant_status(tenant_name):
    """Obtém o status de um tenant"""
    try:
        tenant = frappe.get_doc("SAAS Tenant", tenant_name)
        return {
            "status": "success",
            "data": {
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "state": tenant.state,
                "container_status": tenant.container_status,
                "access_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}",
                "admin_url": f"http://{tenant.subdomain}.localhost:{tenant.container_port if tenant.container_port else 8000}/app",
                "created_at": tenant.creation
            }
        }
    except Exception as e:
        frappe.log_error(f"Erro ao obter status do tenant: {str(e)}")
        return {"status": "error", "message": str(e)}
