HOST = '0.0.0.0:8000'
VERSION = 'v2'
PROTOCOL = "http"
API_URL = "{protocol}://{host}".format(protocol=PROTOCOL, host=HOST)
API_TOKEN = None  # set by wiredrive.auth.set_token()
SSL_VERIFY = True

# Any requests for more resources than the limit will be clamped down to it.
MAX_PAGINATION_LIMIT = 500

RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
# Used for converting to and from datetimes in the fields
DATETIME_FORMAT = RFC3339_FORMAT
