from conductor.client.configuration.configuration import Configuration


def get_configuration():
    configuration = Configuration()
    configuration.debug = False
    configuration.apply_logging_config()

    return configuration
