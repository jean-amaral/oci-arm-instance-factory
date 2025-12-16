import oci


class OCIConfig:
    """
    Wrapper simples sobre o config do OCI SDK.
    """

    def __init__(self, profile: str = "DEFAULT", config_file: str = "~/.oci/config"):
        self._config = oci.config.from_file(
            file_location=config_file,
            profile_name=profile
        )

    @property
    def sdk_config(self) -> dict:
        """
        Retorna o dicionário esperado pelo OCI SDK.
        """
        return self._config

    @property
    def tenancy_id(self) -> str:
        return self._config.get("tenancy")

    @property
    def region(self) -> str:
        return self._config.get("region")
