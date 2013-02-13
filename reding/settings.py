import redis

import os

REDIS_CONFIG = {
    'host': os.getenv('REDING_REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDING_REDIS_PORT', 6379)),
}

TEST_REDIS_CONFIG = {
    'host': os.getenv('REDING_TEST_REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDING_TEST_REDIS_PORT', 6379)),
}

rclient = redis.StrictRedis(**REDIS_CONFIG)
rtest_client = redis.StrictRedis(**TEST_REDIS_CONFIG)

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
    'host': os.getenv('REDING_DAEMON_HOST', '0.0.0.0'),
    'port': int(os.getenv('REDING_DAEMON_HOST', 5000)),
}

KEY_CONFIG = {
    'prefix': 'rating',
    'subject': 'user',
    'object': 'app',
    'subjects': 'users',
    'objects': 'apps'
}

__all__ = (REDIS_CONFIG, DAEMON_CONFIG, KEY_CONFIG)
