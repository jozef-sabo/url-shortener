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
    if config.enabled:
        app.wsgi_app = ProxyFix(
            app=app.wsgi_app,
            x_for=config.x_for, x_proto=config.x_proto, x_host=config.x_host,
            x_port=config.x_port, x_prefix=config.x_prefix
        )
