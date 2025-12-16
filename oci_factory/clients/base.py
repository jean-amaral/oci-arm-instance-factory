class BaseClient:

    def __init__(self, config):
        # Sempre usamos o dict compatível com o SDK
        self.config = config.sdk_config
