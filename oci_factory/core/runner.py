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
        
        self.compartment_id = compartment_id
        self.subnet_id = subnet_id
        self.image_id = image_id
        self.ssh_key_path = ssh_public_key_path
        
        self.shape = shape
        self.ocpus = ocpus
        self.memory = memory
        self.name_prefix = display_name_prefix
        self.poll_interval = poll_interval

        self.state = FactoryState()
        self.availability_domains = self._load_ads()
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
        self.state.add_log("=== Factory Iniciada (Proteção Rate-Limit 5min) ===")
        self.state.update(status="running")

        while True:
            # 1. Verifica pendências
            pending_nodes = []
            for node_name in self.targets:
                if self.state.nodes[node_name]["status"] != "created":
                    pending_nodes.append(node_name)

            # 2. Se acabou, sucesso
            if not pending_nodes:
                self.state.add_log("🏆 MISSÃO CUMPRIDA: Todas as instâncias criadas!")
                self.state.update(status="success", last_message="Factory Finalizada")
                while True: time.sleep(3600)

            # 3. Processa pendentes
            for node_name in pending_nodes:
                self.state.update_node(node_name, status="running", last_msg="Preparando...")
                
                created = False
                for ad in self.availability_domains:
                    self.state.update_node(node_name, status="running", last_msg=f"Testando {ad.name}...")
                    
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
                        
                        self.state.add_log(f"[{node_name}] Request -> {ad.name}")
                        self.compute.launch_instance(request)
                        
                        # Sucesso
                        self.state.add_log(f"✅ SUCESSO: {node_name} criada!")
                        self.state.update_node(node_name, status="created", last_msg=f"Criada no {ad.name}")
                        created = True
                        break 

                    except Exception as e:
                        msg = str(e)
                        
                        # === LÓGICA DE PROTEÇÃO ===
                        if "429" in msg or "TooManyRequests" in msg:
                            # Se der Rate Limit, para TUDO por 5 minutos
                            self.state.add_log(f"🛑 Rate Limit (429). Pausando 5 min para esfriar...")
                            self.state.update_node(node_name, status="waiting", last_msg="Cooldown 5min (Rate Limit)")
                            
                            time.sleep(300)
                            
                            break 
                        
                        elif "Out of host capacity" in msg or "500" in msg:
                            # Erro de capacidade: espera 1.5s e tenta o próximo
                            time.sleep(1.5)
                        
                        else:
                            # Erros genéricos
                            self.state.add_log(f"❌ Erro {node_name}: {msg}")
                            time.sleep(5)

                if not created:

                    self.state.update_node(node_name, status="waiting", last_msg="Aguardando...")

            # Fim do ciclo normal
            self.state.add_log(f"Ciclo concluído. Aguardando {self.poll_interval}s...")
            time.sleep(self.poll_interval)