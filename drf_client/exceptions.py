class APIException(RuntimeError):
    """Include additional information from the response on failed requests."""

    def __init__(self, message, response):
        self.message = message
        self.response = response

    def __str__(self):
        text = self.response.text
        if text:
            return "{}. Response: {}".format(self.message, text)
        else:
            return self.message
