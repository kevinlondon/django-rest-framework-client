from drf_client.auth import AuthenticationBase

HOST = '0.0.0.0:8000'
USE_HTTPS = False
VERIFY_SSL = True
API_URL = "http://{host}".format(host=HOST)

MAX_PAGINATION = 500

RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATETIME_FORMAT = RFC3339_FORMAT

RESPONSE_PARSER = "drf_client.utils.ResponseParser"

AUTHENTICATION = AuthenticationBase()  # set by drf_client.auth
