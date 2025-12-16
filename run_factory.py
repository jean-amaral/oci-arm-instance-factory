import os
import sys
import time
from oci_factory.core.config import OCIConfig
from oci_factory.clients.identity import IdentityClient
from oci_factory.clients.compute import ComputeClient
from oci_factory.core.runner import InstanceFactoryRunner
from oci_factory.utils.logging import setup_logging

setup_logging()

# Carrega variáveis de ambiente (definidas no .env)
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID")
SUBNET_ID = os.getenv("OCI_SUBNET_ID")
IMAGE_ID = os.getenv("OCI_IMAGE_ID")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")

SHAPE = os.getenv("INSTANCE_SHAPE", "VM.Standard.A1.Flex")
OCPUS = int(os.getenv("INSTANCE_OCPUS", 1))
MEMORY_GB = int(os.getenv("INSTANCE_MEMORY_GB", 6))

def main():
    print("=== OCI Instance Factory Iniciado ===")
    
    if not COMPARTMENT_ID or not SUBNET_ID or not IMAGE_ID:
        print("ERRO: Variáveis de ambiente OCI_COMPARTMENT_ID, OCI_SUBNET_ID ou OCI_IMAGE_ID não encontradas.")
        print("Verifique se o arquivo .env existe e se o systemd está configurado corretamente.")
        sys.exit(1)

    try:
        oci_config = OCIConfig(profile="DEFAULT") 

        identity_client = IdentityClient(oci_config)
        compute_client = ComputeClient(oci_config)

        runner = InstanceFactoryRunner(
            identity_client=identity_client,
            compute_client=compute_client,
            compartment_id=COMPARTMENT_ID,
            subnet_id=SUBNET_ID,
            image_id=IMAGE_ID,
            shape=SHAPE,
            ocpus=OCPUS,
            memory=MEMORY_GB,
            ssh_public_key_path=SSH_KEY_PATH,
            poll_interval=60
        )

        runner.start()

    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()