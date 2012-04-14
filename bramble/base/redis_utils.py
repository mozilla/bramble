from django.conf import settings
from django.core.cache import parse_backend_uri

from redis import Redis, ConnectionError


class RedisError(Exception):
    """An error with the redis configuration or connnection."""


def RetryForeverWrapper(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ConnectionError:
            how_long = 1
            logging.warning("connection error, sleeping %s seconds", how_long)
            sleep(how_long)
            self.__call__(*args, **kwargs)
    return wrapper


class RetryForeverRedis(object):
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        return RetryForeverWrapper(getattr(self.obj, name))


def redis_client(name):
    """Get a Redis client.

    Uses the name argument to lookup the connection string in the
    settings.REDIS_BACKEND dict.
    """
    if name not in settings.REDIS_BACKENDS:
        raise RedisError(
            '{k} is not defined in settings.REDIS_BACKENDS'.format(k=name))

    uri = settings.REDIS_BACKENDS[name]
    _, server, params = parse_backend_uri(uri)
    db = params.pop('db', 1)
    try:
        db = int(db)
    except (ValueError, TypeError):
        db = 1
    try:
        socket_timeout = float(params.pop('socket_timeout'))
    except (KeyError, ValueError):
        socket_timeout = None
    password = params.pop('password', None)
    if ':' in server:
        host, port = server.split(':')
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 6379
    else:
        host = server
        port = 6379
    redis = Redis(host=host, port=port, db=db, password=password,
                  socket_timeout=socket_timeout)
    try:
        # Make a cheap call to verify we can connect.
        redis.exists('dummy-key')
    except ConnectionError:
        raise RedisError(
            'Unable to connect to redis backend: {k}'.format(k=name))
    return RetryForeverRedis(redis)
