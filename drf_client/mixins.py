from drf_client import api


class CreateMixin(object):

    @classmethod
    def create(cls, *args, **kwargs):
        return api.create(cls=cls, *args, **kwargs)


class GetMixin(object):

    @classmethod
    def get(cls, *args, **kwargs):
        return api.get(cls=cls, *args, **kwargs)
