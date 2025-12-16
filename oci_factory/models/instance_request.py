from dataclasses import dataclass


@dataclass
class InstanceRequest:
    compartment_id: str
    availability_domain: str
    shape: str
    subnet_id: str
    image_id: str
    display_name: str
    ocpus: int = 1
    memory_gbs: int = 6
