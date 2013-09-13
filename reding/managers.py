from datetime import datetime
import redis
from reding.settings import KEY_CONFIG, REDIS_CONFIG
rclient = redis.StrictRedis(**REDIS_CONFIG)


def get_key_name(template, **kw):
    d = KEY_CONFIG.copy()
    d.update(dict((key, value) for (key, value) in kw.iteritems() if value))
    return template.format(**d)


def zrange(start, end, reverse):
    if not reverse:
        return rclient.zrangebyscore, start, end
    else:
        return rclient.zrevrangebyscore, end, start


class ObjectSubjectsManager(object):
    def __init__(self, **kwargs):
        self.template = get_key_name('{prefix}:{object}:{{object_id}}:{subjects}', **kwargs)
        self.template_review = get_key_name('{prefix}:{object}:{{object_id}}:review:{subjects}', **kwargs)

    def count(self, object_id, min_vote='-inf', max_vote='+inf'):
        return rclient.zcount(
            name=self.template.format(object_id=object_id),
            min=min_vote,
            max=max_vote,
        )

    def scoredrange(self, object_id, offset, size, min_vote='-inf', max_vote='+inf', reverse=False):
        func, min_vote, max_vote = zrange(min_vote, max_vote, reverse)
        return func(
            name=self.template.format(object_id=object_id),
            min=min_vote,
            max=max_vote,
            start=offset,
            num=size,
            withscores=True,
        )

    def score(self, object_id, user_id):
        return rclient.zscore(
            name=self.template.format(object_id=object_id),
            value=user_id,
        )

    def review(self, object_id, user_id):
        return rclient.hget(
            name=self.template_review.format(object_id=object_id),
            key=user_id,
        )

    def reviews(self, object_id, *user_ids):
        return dict(zip(user_ids, rclient.hmget(
            self.template_review.format(object_id=object_id), user_ids
        )))

    def create(self, object_id, user_id, vote, review):
        rclient.zadd(
            self.template.format(object_id=object_id),
            vote,
            user_id,
        )
        name = self.template_review.format(object_id=object_id)
        if review:
            rclient.hset(name, user_id, review)
        else:
            rclient.hdel(name, user_id)

    def remove(self, object_id, user_id):
        rclient.zrem(
            self.template.format(object_id=object_id),
            user_id,
        )
        rclient.hdel(
            self.template_review.format(object_id=object_id),
            user_id,
        )


class SubjectObjectsManager(object):
    def __init__(self, **kwargs):
        self.template = get_key_name('{prefix}:{subject}:{{user_id}}:{objects}', **kwargs)

    def scoredrange(self, user_id, offset, size, min_vote='-inf', max_vote='+inf', reverse=False):
        func, min_vote, max_vote = zrange(min_vote, max_vote, reverse)
        scored = func(
            name=self.template.format(user_id=user_id),
            min=min_vote,
            max=max_vote,
            start=offset,
            num=size,
            withscores=True,
        )
        return [(k, datetime.fromtimestamp(v)) for k, v in scored]

    def score(self, user_id, object_id):
        try:
            return datetime.fromtimestamp(rclient.zscore(
                name=self.template.format(user_id=user_id),
                value=object_id,
            ))
        except TypeError:
            return 0

    def create(self, user_id, object_id, timestamp):
        rclient.zadd(
            self.template.format(user_id=user_id),
            timestamp,
            object_id,
        )

    def remove(self, user_id, object_id):
        rclient.zrem(
            self.template.format(user_id=user_id),
            object_id,
        )


class ObjectsManager(object):
    def __init__(self, **kwargs):
        self.template = get_key_name('{prefix}:{objects}', **kwargs)

    def scoredrange(self, offset, size, min_vote='-inf', max_vote='+inf', reverse=False):
        func, min_vote, max_vote = zrange(min_vote, max_vote, reverse)
        return func(
            name=self.template,
            min=min_vote,
            max=max_vote,
            start=offset,
            num=size,
            withscores=True,
        )

    def score(self, object_id):
        return rclient.zscore(
            name=self.template,
            value=object_id,
        )

    def incrby(self, object_id, delta):
        rclient.zincrby(
            name=self.template,
            value=object_id,
            amount=delta,
        )

    def remove(self, object_id):
        rclient.zrem(
            self.template,
            object_id,
        )

    def filtered(self, objects, now, reverse):
        if not objects:
            return []

        tmp_key = '{0}:tmp:{1}'.format(self.template, now)
        tmp_dest_key = '{0}:tmp_dest:{1}'.format(self.template, now)

        rclient.sadd(tmp_key, *objects)
        rclient.zinterstore(tmp_dest_key, (self.template, tmp_key), aggregate='SUM')

        if reverse:
            zsorted = rclient.zrevrangebyscore(tmp_dest_key, '+inf', '-inf')
        else:
            zsorted = rclient.zrangebyscore(tmp_dest_key, '-inf', '+inf')

        rclient.delete(tmp_key, tmp_dest_key)

        return zsorted + list(set(objects).difference(set(zsorted)))
