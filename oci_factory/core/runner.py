import time
import logging
from oci_factory.core.state import FactoryState
from oci_factory.models.instance_request import InstanceRequest

class InstanceFactoryRunner:
    def __init__(
        self,
        identity_client,
        compute_client,
        compartment_id: str,
        subnet_id: str,
        image_id: str,
        shape: str,
        ocpus: int,
        memory: int,
        ssh_public_key_path: str,
        display_name_prefix: str = "bot-arm",
        poll_interval: int = 60
    ):
        self.identity = identity_client
        self.compute = compute_client
        
        # Dados da infra
        self.compartment_id = compartment_id
        self.subnet_id = subnet_id
        self.image_id = image_id
        self.ssh_key_path = ssh_public_key_path
        
        # Specs (Default Boot Volume ~47GB/50GB é padrão da imagem)
        self.shape = shape
        self.ocpus = ocpus
        self.memory = memory
        self.name_prefix = display_name_prefix
        self.poll_interval = poll_interval

        self.state = FactoryState()
        self.availability_domains = self._load_ads()
        
        # Define os alvos (Nodes) que queremos criar
        self.targets = ["Instancia-1", "Instancia-2"]

    def _load_ads(self):
        try:
            ads = self.identity.list_availability_domains()
            self.state.add_log(f"ADs detectados: {len(ads)}")
            return ads
        except Exception as e:
            self.state.add_log(f"Erro ao listar ADs: {e}")
            return []

    def start(self):
        self.state.add_log("=== Factory Iniciada (Modo Multi-Nó) ===")
        # Garante que o status global comece como Rodando
        self.state.update(status="running")

        while True:
            active_attempts = 0
            
            # 1. Verifica quais nós ainda precisam ser criados
            pending_nodes = []
            for node_name in self.targets:
                # Se status não é 'created', adiciona na lista de pendentes
                if self.state.nodes[node_name]["status"] != "created":
                    pending_nodes.append(node_name)

            # 2. Se não há pendentes, ACABOU!
            if not pending_nodes:
                # Trava de Segurança: Missão Cumprida
                self.state.add_log("🏆 MISSÃO CUMPRIDA: Todas as instâncias criadas!")
                self.state.update(
                    status="success", 
                    last_message="Factory Finalizada com Sucesso"
                )
                
                # Entra em loop de hibernação longa para não matar o processo
                # (Isso mantém o dashboard acessível mostrando 'Sucesso')
                while True:
                    time.sleep(3600) # Dorme por 1 hora repetidamente

            # 3. Se há pendentes, continua o trabalho
            active_attempts = len(pending_nodes)
            
            for node_name in pending_nodes:
                self.state.update_node(node_name, status="running", last_msg="Iniciando ciclo...")
                
                created = False
                for ad in self.availability_domains:
                    self.state.update_node(node_name, last_msg=f"Tentando no {ad.name}")
                    
                    try:
                        request = InstanceRequest(
                            compartment_id=self.compartment_id,
                            availability_domain=ad.name,
                            shape=self.shape,
                            subnet_id=self.subnet_id,
                            image_id=self.image_id,
                            display_name=f"{self.name_prefix}-{node_name}",
                            ocpus=self.ocpus,
                            memory_gbs=self.memory
                        )
                        
                        self.state.add_log(f"[{node_name}] Request -> {ad.name}...")
                        self.compute.launch_instance(request)
                        
                        # Sucesso neste nó
                        self.state.add_log(f"✅ SUCESSO: {node_name} criada no {ad.name}!")
                        self.state.update_node(node_name, status="created", last_msg=f"Criada no {ad.name}")
                        created = True
                        break # Sai do loop de ADs para este nó

                    except Exception as e:
                        msg = str(e)
                        if "Out of host capacity" in msg or "500" in msg:
                            # Log discreto para erro comum
                            pass 
                        else:
                            self.state.add_log(f"❌ Erro {node_name}: {msg}")

                if not created:
                    self.state.update_node(node_name, status="waiting", last_msg="Sem capacidade (Aguardando)")

            # Fim do ciclo de tentativas
            self.state.add_log(f"Ciclo finalizado. {active_attempts} nós pendentes. Aguardando {self.poll_interval}s...")
            time.sleep(self.poll_interval)