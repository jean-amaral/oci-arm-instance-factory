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
        self.state.add_log("=== Factory Iniciada (Modo Sequencial + Delay ADs) ===")
        self.state.update(status="running")

        while True:
            current_target = None
            
            # Lógica Sequencial Estrita (Foco na 1, depois na 2)
            if self.state.nodes["Instancia-1"]["status"] != "created":
                current_target = "Instancia-1"
                if self.state.nodes["Instancia-2"]["status"] != "created":
                    self.state.update_node("Instancia-2", status="waiting", last_msg="Aguardando Instancia-1...")
            
            elif self.state.nodes["Instancia-2"]["status"] != "created":
                current_target = "Instancia-2"
            
            else:
                self.state.add_log("🏆 MISSÃO CUMPRIDA: Todas as instâncias criadas!")
                self.state.update(status="success", last_message="Factory Finalizada")
                while True: time.sleep(3600)

            if current_target:
                node_name = current_target
                self.state.update_node(node_name, status="running", last_msg="Iniciando ciclo...")
                
                created = False
                
                # Loop pelos ADs (com Delay Tático entre eles)
                for i, ad in enumerate(self.availability_domains):
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
                        
                        self.state.add_log(f"✅ SUCESSO: {node_name} criada!")
                        self.state.update_node(node_name, status="created", last_msg=f"Criada no {ad.name}")
                        created = True
                        break 

                    except Exception as e:
                        msg = str(e)
                        
                        # Tratamento Crítico de Rate Limit (429)
                        if "429" in msg or "TooManyRequests" in msg:
                            self.state.add_log(f"🛑 Rate Limit (429). Pausando 5 min...")
                            self.state.update_node(node_name, status="waiting", last_msg="Cooldown 5min (Rate Limit)")
                            time.sleep(300) 
                            break 
                        
                        elif "Out of host capacity" in msg or "500" in msg:
                            # Falha normal de capacidade. Não fazemos sleep aqui, 
                            # pois o sleep maior virá no final do bloco do AD.
                            pass
                        
                        else:
                            self.state.add_log(f"❌ Erro {node_name}: {msg}")
                    
                    # === DELAY TÁTICO ENTRE ADs ===
                    # Se não foi criada e não é o último AD da lista, espera um pouco antes de tentar o próximo.
                    if not created and i < len(self.availability_domains) - 1:
                        self.state.add_log(f"⏳ Aguardando 10s para tentar próximo AD...")
                        time.sleep(10) # <--- O SEGREDO ESTÁ AQUI

                if not created:
                    self.state.update_node(node_name, status="waiting", last_msg="Sem capacidade (Aguardando)")

            self.state.add_log(f"Ciclo concluído. Aguardando {self.poll_interval}s...")
            time.sleep(self.poll_interval)