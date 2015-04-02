# -*- coding: utf-8 -*-

__author__ = 'Kevin London'
__email__ = 'kevin@wiredrive.com'
__version__ = '0.1.0'


def configure(filepath=None):
    import yaml
    with open(filepath, 'r') as config_file:
        config = yaml.load(config_file)

    from . import settings
    for key, value in config.items():
        setattr(settings, key, value)

    scheme = "https" if settings.USE_HTTPS else "http"
    settings.API_URL = "{0}://{1}".format(scheme, settings.HOST)
