# -*- coding: utf-8 -*-

__author__ = 'Kevin London'
__email__ = 'kevin@wiredrive.com'
__version__ = '0.1.0'


def configure(filepath=None, username=None, password=None, token=None):
    import yaml
    from . import settings

    with open(filepath, 'r') as config_file:
        config = yaml.load(config_file)

    for key, value in config.items():
        setattr(settings, key, value)

    scheme = "https" if settings.USE_HTTPS else "http"
    settings.API_URL = "{0}://{1}".format(scheme, settings.HOST)
    authenticate(username, password, token)


def authenticate(username, password, token):
    from . import auth
    import logging
    logger = logging.getLogger(__name__)

    if username:
        auth.log_in(username=username, password=password)
    elif token:
        auth.set_token(token=token)
    else:
        logger.warning("No authentication provided to configuration.")
