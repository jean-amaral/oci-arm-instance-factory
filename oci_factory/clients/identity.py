import oci
from oci_factory.clients.base import BaseClient


class IdentityClient(BaseClient):

    def __init__(self, config: dict):
        super().__init__(config)
        self.client = oci.identity.IdentityClient(self.config)

    def list_availability_domains(self):
        response = self.client.list_availability_domains(
            compartment_id=self.config["tenancy"]
        )
        return response.data
