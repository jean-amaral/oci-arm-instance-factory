import oci

from oci.core.models import (
    LaunchInstanceDetails,
    CreateVnicDetails,
    InstanceSourceViaImageDetails
)

from oci_factory.clients.base import BaseClient
from oci_factory.models.instance_request import InstanceRequest


class ComputeClient(BaseClient):

    def __init__(self, config):
        super().__init__(config)
        self.client = oci.core.ComputeClient(self.config)

    def list_shapes(self, compartment_id, availability_domain):
        response = self.client.list_shapes(
            compartment_id=compartment_id,
            availability_domain=availability_domain
        )
        return response.data

    def launch_instance(self, request: InstanceRequest):
        source_details = InstanceSourceViaImageDetails(
            image_id=request.image_id
        )

        launch_details = LaunchInstanceDetails(
            compartment_id=request.compartment_id,
            availability_domain=request.availability_domain,
            shape=request.shape,
            display_name=request.display_name,
            create_vnic_details=CreateVnicDetails(
                subnet_id=request.subnet_id,
                assign_public_ip=True
            ),
            source_details=source_details,
            shape_config={
                "ocpus": request.ocpus,
                "memory_in_gbs": request.memory_gbs
            }
        )

        return self.client.launch_instance(launch_details)
