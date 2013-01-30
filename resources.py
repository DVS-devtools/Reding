from flask.ext.restful import reqparse, fields, marshal_with  # , abort
from flask.ext import restful

from time import time
from datetime import datetime

from settings import KEY_CONFIG, rclient


def add_config_args(parser):
    for k in KEY_CONFIG:
        parser.add_argument(k, type=str)


def get_user_object_reply(subject_id, object_id, vote, when):
    return {
        'subject_id': subject_id,
        'object_id': object_id,
        'vote': vote,
        'when': when,
    }


def get_user_key_name(**kw):
    t = "{prefix}:{object_type}:{object_id}:{subject_types}"
    return get_key_name(t, **kw)


def get_object_key_name(**kw):
    t = "{prefix}:{subject_types}"
    return get_key_name(t, **kw)


def get_user_object_key_name(**kw):
    t = "{prefix}:{subject_type}:{subject_id}:{object_types}"
    return get_key_name(t, **kw)


def get_key_name(template, **kw):
    try:
        kw = {key: value for (key, value) in kw.iteritems() if value}
    except:
        kw = dict((key, value) for (key, value) in kw.iteritems() if value)

    d = KEY_CONFIG.copy()
    d.update(kw)

    return template.format(**d)


# TODO: add tests, need 404?
# def abort_if_todo_doesnt_exist(todo_id):
    #if todo_id not in TODOS:
        #abort(404, message="Todo {} doesn't exist".format(todo_id))

object_resource_fields = {
    'votes_no': fields.Integer,
    'amount': fields.Integer,
    'average': fields.Float,
    'subject_id': fields.String,
}

user_object_resource_fields = {
    'vote': fields.Integer,
    'subject_id': fields.String,
    'object_id': fields.String,
    'when': fields.DateTime
}


class ObjectList(restful.Resource):

    redis = rclient
    parser = reqparse.RequestParser()

    def __init__(self):
        super(Object, self).__init__()
        add_config_args(self.parser)

    @marshal_with(object_resource_fields)
    def get(self):
        amounts = self.redis.zrangebyscore(
            get_object_key_name(),
            '-inf',
            '+inf',
            withscores=True,
        )

        reply = []
        for s, a in amounts:
            n = self.redis.zcount(
                get_user_object_key_name(
                    subject_id=s,
                ),
                '-inf',
                '+inf',
            )
            reply.append(
                dict(
                    votes_no=n,
                    average=a/n,
                    amount=a,
                    subject_id=s,
                )
            )

        return reply


class Object(restful.Resource):

    redis = rclient
    parser = reqparse.RequestParser()

    def __init__(self):
        super(Object, self).__init__()
        add_config_args(self.parser)
        self.parser.add_argument('vote', type=int)

    @marshal_with(object_resource_fields)
    def get(self, subject_id):
        args = self.parser.parse_args()

        vote = args['vote']

        amount = self.redis.zscore(
            get_object_key_name(**args),
            subject_id,
        )

        min = '-inf'
        max = '+inf'
        if vote:
            min = vote
            max = vote

        number = self.redis.zcount(
            get_user_object_key_name(
                subject_id=subject_id,
                **args
            ),
            min,
            max,
        )

        if not number:
            average = 0
            amount = 0
        elif vote:
            average = vote
            amount = vote*number
        else:
            average = amount/number

        return (
            dict(
                votes_no=number,
                average=average,
                amount=amount,
                subject_id=subject_id,
            )
        )


class ObjectUsers(restful.Resource):

    redis = rclient
    parser = reqparse.RequestParser()

    def __init__(self):
        super(Object, self).__init__()
        add_config_args(self.parser)

    @marshal_with(user_object_resource_fields)
    def get(self, subject_id):
        args = self.parser.parse_args()

        votes = self.redis.zrangebyscore(
            get_user_object_key_name(
                subject_id=subject_id,
                **args
            ),
            '-inf',
            '+inf',
            withscores=True,
        )

        reply = [
            get_user_object_reply(
                subject_id=subject_id,
                object_id=o,
                vote=v,
                when=datetime.fromtimestamp(
                    self.redis.zscore(
                        get_user_key_name(
                            object_id=o,
                            **args
                        ),
                        subject_id,
                    ),
                ),
            ) for o, v in votes
        ]

        return reply


class UserList(restful.Resource):

    redis = rclient
    parser = reqparse.RequestParser()

    def __init__(self):
        super(Object, self).__init__()
        add_config_args(self.parser)

    @marshal_with(user_object_resource_fields)
    def get(self, object_id):
        args = self.parser.parse_args()

        votetimes = self.redis.zrangebyscore(
            get_user_key_name(
                object_id=object_id,
                **args
            ),
            '-inf',
            '+inf',
            withscores=True,
        )

        reply = [
            get_user_object_reply(
                subject_id=a,
                object_id=object_id,
                vote=self.redis.zscore(
                    get_user_object_key_name(
                        subject_id=a,
                        **args
                    ),
                    object_id,
                ),
                when=datetime.fromtimestamp(
                    self.redis.zscore(
                        get_user_key_name(
                            object_id=object_id,
                            **args
                        ),
                        a,
                    ),
                )
            ) for a, t in votetimes
        ]

        return reply


class UserObject(restful.Resource):

    redis = rclient
    parser = reqparse.RequestParser()

    def __init__(self):
        super(UserObject, self).__init__()
        add_config_args(self.parser)
        self.parser.add_argument('vote', type=int)

    @marshal_with(user_object_resource_fields)
    def get(self, subject_id, object_id):
        args = self.parser.parse_args()

        return get_user_object_reply(
            subject_id=subject_id,
            object_id=object_id,
            vote=self.redis.zscore(
                get_user_object_key_name(
                    subject_id=subject_id,
                    **args
                ),
                object_id,
            ),
            when=datetime.fromtimestamp(
                self.redis.zscore(
                    get_user_key_name(
                        object_id=object_id,
                        **args
                    ),
                    subject_id,
                ),
            )
        )

    def post(self, subject_id, object_id):
        return self.put(subject_id, object_id)

    @marshal_with(user_object_resource_fields)
    def put(self, subject_id, object_id):
        args = self.parser.parse_args()

        next_vote = args['vote']

        prev_vote = self.redis.zscore(
            get_user_object_key_name(
                subject_id=subject_id,
                **args
            ),
            object_id,
        )

        if not prev_vote:
            prev_vote = 0

        correction = next_vote - prev_vote

        # perform vote correction in `all apps` zset
        if correction:
            self.redis.zincrby(
                get_object_key_name(**args),
                subject_id,
                correction,
            )

        self.redis.zadd(
            get_user_object_key_name(
                subject_id=subject_id,
                **args
            ),
            next_vote,
            object_id,
        )

        self.redis.zadd(
            get_user_key_name(
                object_id=object_id,
                **args
            ),
            time(),
            subject_id,
        )

        return get_user_object_reply(
            subject_id=subject_id,
            object_id=object_id,
            vote=self.redis.zscore(
                get_user_object_key_name(
                    subject_id=subject_id,
                    **args
                ),
                object_id,
            ),
            when=datetime.fromtimestamp(
                self.redis.zscore(
                    get_user_key_name(
                        object_id=object_id,
                        **args
                    ),
                    subject_id,
                ),
            )
        )

    @marshal_with(user_object_resource_fields)
    def delete(self, subject_id, object_id):
        args = self.parser.parse_args()

        self.redis.zrem(
            get_user_object_key_name(
                subject_id=subject_id,
                **args
            ),
            object_id,
        )

        return '', 204

__all__ = (Object, ObjectList, ObjectUsers, UserObject, UserList)
