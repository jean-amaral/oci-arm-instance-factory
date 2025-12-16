import time
import logging
from oci_factory.core.state import FactoryState


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
        poll_interval: int = 60,
        state_file: str = "/home/ubuntu/oci-factory/state.json"
    ):
        self.identity = identity_client
        self.compute = compute_client
        self.compartment_id = compartment_id
        self.subnet_id = subnet_id
        self.image_id = image_id
        self.shape = shape
        self.ocpus = ocpus
        self.memory = memory
        self.ssh_key_path = ssh_public_key_path
        self.poll_interval = poll_interval

        self.state = FactoryState(state_file)

        self.availability_domains = self._load_ads()
        self.attempt = 0

    def _load_ads(self):
        ads = self.identity.list_availability_domains()
        logging.info(
            "ADs detectados: %s",
            ", ".join(ad.name for ad in ads)
        )
        return ads

    def start(self):
        logging.info("Factory iniciada")
        self.state.update(status="running")

        while True:
            self.attempt += 1
            logging.info("Tentativa #%d", self.attempt)
            self.state.update(attempt=self.attempt)

            for ad in self.availability_domains:
                logging.info("→ Tentando no AD %s", ad.name)
                self.state.update(
                    current_ad=ad.name,
                    last_message="Tentando criar instância"
                )

                try:
                    self.compute.launch_instance(
                        compartment_id=self.compartment_id,
                        subnet_id=self.subnet_id,
                        image_id=self.image_id,
                        availability_domain=ad.name,
                        shape=self.shape,
                        ocpus=self.ocpus,
                        memory=self.memory,
                        ssh_public_key_path=self.ssh_key_path
                    )

                    logging.info("✅ Instância criada com sucesso")
                    self.state.update(
                        status="success",
                        last_message="Instância criada com sucesso"
                    )
                    return

                except Exception as e:
                    msg = str(e)
                    if "Out of host capacity" in msg:
                        logging.warning("⚠️ Sem capacidade neste AD")
                        self.state.update(
                            last_message="Sem capacidade neste AD"
                        )
                    else:
                        logging.error("Erro ao criar instância: %s", msg)
                        self.state.update(
                            last_message=f"Erro: {msg}"
                        )

            logging.info("Aguardando %ds para nova rodada...", self.poll_interval)
            self.state.update(
                last_message=f"Aguardando {self.poll_interval}s para nova rodada"
            )
            time.sleep(self.poll_interval)
