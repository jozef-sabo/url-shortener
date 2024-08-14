import logging

from werkzeug.middleware.proxy_fix import ProxyFix

from config import Proxy


def init(app, config: Proxy) -> None:
    """
    Initializes reverse proxy fix if enabled based on a given config

    Contains FEATURE SWITCH
    :param app: Flask app object
    :param config: Proxy object of a configuration containing information
    :return: None
    """
    logging.debug("Going to initialize proxy, state %s", config.enabled)
    if config.enabled:
        app.wsgi_app = ProxyFix(
            app=app.wsgi_app,
            x_for=config.x_for, x_proto=config.x_proto, x_host=config.x_host,
            x_port=config.x_port, x_prefix=config.x_prefix
        )
        logging.debug("Proxy initialized with values x_for=%s, x_proto=%s, x_host=%s, x_port=%s, x_prefix=%s",
                      config.x_for, config.x_proto, config.x_host, config.x_port, config.x_prefix)
