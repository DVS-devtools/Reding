import os

REDIS_CONFIG = {
    'host': os.getenv('REDING_REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDING_REDIS_PORT', 6379)),
    'db': int(os.getenv('REDING_REDIS_DB', 0)),
}

DAEMON_CONFIG = {
    'host': os.getenv('REDING_DAEMON_HOST', '0.0.0.0'),
    'port': int(os.getenv('REDING_DAEMON_PORT', 5000)),
}

KEY_CONFIG = {
    'prefix': 'rating',
    'subject': 'user',
    'object': 'app',
    'subjects': 'users',
    'objects': 'apps'
}

PAGINATION_DEFAULT_OFFSET = 0
PAGINATION_DEFAULT_SIZE = 10

__all__ = (
    'REDIS_CONFIG',
    'DAEMON_CONFIG',
    'KEY_CONFIG',
)
