import redis

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
}

rclient = redis.StrictRedis(**REDIS_CONFIG)

# TODO: add nydus
# from nydus.db import create_cluster
#
#redis = create_cluster({
#    'backend': 'nydus.db.backends.redis.Redis',
#    'hosts': {
#        0: {'db': 0},
#    }
#})

DAEMON_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
}

KEY_CONFIG = {
    'prefix': 'rating',
    'subject': 'user',
    'object': 'app',
    'subjects': 'users',
    'objects': 'apps'
}

__all__ = (REDIS_CONFIG, DAEMON_CONFIG, KEY_CONFIG)
