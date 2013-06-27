from reding.settings import KEY_CONFIG, rclient
from reding.settings import PAGINATION_DEFAULT_OFFSET as OFFSET
from reding.settings import PAGINATION_DEFAULT_SIZE as SIZE

from flask.ext.restful import reqparse, fields, marshal_with, abort
from flask.ext import restful

from time import time
from datetime import datetime


def add_vote_arg(parser, required=False):
    parser.add_argument('vote', type=int, required=required, default=0)


def add_config_args(parser):
    for k in KEY_CONFIG:
        parser.add_argument(k, type=str)


def get_user_object_reply(object_id, user_id, vote, when):
    return {
        'object_id': object_id,
        'user_id': user_id,
        'vote': vote,
        'when': when,
    }


def get_user_key_name(**kw):
    t = "{prefix}:{subject}:{user_id}:{objects}"
    return get_key_name(t, **kw)


def get_object_key_name(**kw):
    t = "{prefix}:{objects}"
    return get_key_name(t, **kw)


def get_user_object_key_name(**kw):
    t = "{prefix}:{object}:{object_id}:{subjects}"
    return get_key_name(t, **kw)


def get_key_name(template, **kw):
    kw = dict((key, value) for (key, value) in kw.iteritems() if value)

    d = KEY_CONFIG.copy()
    d.update(kw)

    return template.format(**d)


object_resource_fields = {
    'votes_no': fields.Integer,
    'amount': fields.Integer,
    'average': fields.Float,
    'object_id': fields.String,
}

user_object_resource_fields = {
    'vote': fields.Integer,
    'object_id': fields.String,
    'user_id': fields.String,
    'when': fields.DateTime
}


class RedingResource(restful.Resource):

    redis = rclient
    parser_cls = reqparse.RequestParser

    def __init__(self):
        super(RedingResource, self).__init__()
        self.parser = self.parser_cls()
        add_config_args(self.parser)


class VotedListResource(RedingResource):

    def __init__(self):
        super(VotedListResource, self).__init__()
        self.parser.add_argument('object_id', type=str, action='append')
        self.parser.add_argument('sort', type=str, default='+')
        self.parser.add_argument('offset', type=int, default=OFFSET)
        self.parser.add_argument('size', type=int, default=SIZE)

    @marshal_with(object_resource_fields)
    def get(self):
        args = self.parser.parse_args()

        sort = '+'
        if args['sort'] in ('-', '+'):
            if args['sort'] == '-':
                sort = '-'

        if sort == '+':
            amounts = self.redis.zrangebyscore(
                get_object_key_name(**args),
                '-inf',
                '+inf',
                withscores=True,
                start=args['offset'],
                num=args['size'],
            )
        else:
            amounts = self.redis.zrevrangebyscore(
                get_object_key_name(**args),
                '+inf',
                '-inf',
                withscores=True,
                start=args['offset'],
                num=args['size'],
            )

        reply = []
        for o, a in amounts:
            args['object_id'] = o
            n = self.redis.zcount(
                get_user_object_key_name(
                    **args
                ),
                '-inf',
                '+inf',
            )

            average = 0
            if n:
                average = a / n

                # skipping objects with zero votes
                reply.append(
                    dict(
                        votes_no=n,
                        average=average,
                        amount=a,
                        object_id=o,
                    )
                )

        return reply

    def post(self):
        """
        It sorts a list of 'object_id' with their amount of votes and returns it,
        objects not rated are at the end of the list
        :return: list
        """
        args = self.parser.parse_args()

        sort = '+'
        if args['sort'] in ('-', '+'):
            if args['sort'].startswith('-'):
                sort = '-'

        objects = args['object_id']

        if not objects:
            return []

        tmp_key = '{0}:tmp:{1}'.format(get_object_key_name(**args), int(time()))
        tmp_dest_key = '{0}:tmp_dest:{1}'.format(get_object_key_name(**args), int(time()))

        self.redis.sadd(tmp_key, *objects)
        self.redis.zinterstore(tmp_dest_key, (get_object_key_name(**args), tmp_key), aggregate='SUM')

        if sort == '+':
            sorted = self.redis.zrangebyscore(tmp_dest_key, '-inf', '+inf')
        else:
            sorted = self.redis.zrevrangebyscore(tmp_dest_key, '+inf', '-inf')

        self.redis.delete(tmp_key, tmp_dest_key)

        sorted_set = set(sorted)
        object_set = set(objects)

        return sorted + list(object_set.difference(sorted_set))


class VotedSummaryResource(RedingResource):

    @marshal_with(object_resource_fields)
    def get(self, object_id):
        add_vote_arg(self.parser)
        args = self.parser.parse_args()

        vote = args['vote']

        amount = self.redis.zscore(
            get_object_key_name(**args),
            object_id,
        )

        min_vote = '-inf'
        max_vote = '+inf'
        if vote:
            min_vote = vote
            max_vote = vote

        number = self.redis.zcount(
            get_user_object_key_name(
                object_id=object_id,
                **args
            ),
            min_vote,
            max_vote,
        )

        if not amount:
            amount = 0  # FIXME can test this line with a single vote=0 to a new object
        if not number:
            average = 0
            amount = 0
        elif vote:
            average = vote
            amount = vote * number
        else:
            average = amount / number

        return (
            dict(
                votes_no=number,
                average=average,
                amount=amount,
                object_id=object_id,
            )
        )


class VotingUserListResource(RedingResource):

    def __init__(self):
        super(VotingUserListResource, self).__init__()
        self.parser.add_argument('sort', type=str, default='+')
        self.parser.add_argument('offset', type=int, default=OFFSET)
        self.parser.add_argument('size', type=int, default=SIZE)
        add_vote_arg(self.parser)

    @marshal_with(user_object_resource_fields)
    def get(self, object_id):
        args = self.parser.parse_args()

        sort = '+'
        start = '-inf'
        end = '+inf'
        if args['sort'] in ('-', '+'):
            if args['sort'].startswith('-'):
                sort = '-'
                start = '+inf'
                end = '-inf'

        vote = args['vote']

        if vote:
            start = vote
            end = vote

        if sort == '+':
            votes = self.redis.zrangebyscore(
                get_user_object_key_name(
                    object_id=object_id,
                    **args
                ),
                start,
                end,
                withscores=True,
                start=args['offset'],
                num=args['size'],
            )
        else:
            votes = self.redis.zrevrangebyscore(
                get_user_object_key_name(
                    object_id=object_id,
                    **args
                ),
                start,
                end,
                withscores=True,
                start=args['offset'],
                num=args['size'],
            )

        reply = [
            get_user_object_reply(
                object_id=object_id,
                user_id=u,
                vote=v,
                when=datetime.fromtimestamp(
                    self.redis.zscore(
                        get_user_key_name(
                            user_id=u,
                            **args
                        ),
                        object_id,
                    ),
                ),
            ) for u, v in votes
        ]

        return reply


class UserSummaryResource(RedingResource):

    def __init__(self):
        super(UserSummaryResource, self).__init__()
        self.parser.add_argument('sort', type=str, default='+')
        self.parser.add_argument('offset', type=int, default=OFFSET)
        self.parser.add_argument('size', type=int, default=SIZE)

    @marshal_with(user_object_resource_fields)
    def get(self, user_id):
        args = self.parser.parse_args()

        sort = '+'
        if args['sort'] in ('-', '+'):
            if args['sort'].startswith('-'):
                sort = '-'

        if sort == '+':
            votetimes = self.redis.zrangebyscore(
                get_user_key_name(
                    user_id=user_id,
                    **args
                ),
                '-inf',
                '+inf',
                withscores=True,
                start=args['offset'],
                num=args['size'],
            )
        else:
            votetimes = self.redis.zrevrangebyscore(
                get_user_key_name(
                    user_id=user_id,
                    **args
                ),
                '+inf',
                '-inf',
                withscores=True,
                start=args['offset'],
                num=args['size'],
            )

        reply = [
            get_user_object_reply(
                object_id=o,
                user_id=user_id,
                vote=self.redis.zscore(
                    get_user_object_key_name(
                        object_id=o,
                        **args
                    ),
                    user_id,
                ),
                when=datetime.fromtimestamp(
                    self.redis.zscore(
                        get_user_key_name(
                            user_id=user_id,
                            **args
                        ),
                        o,
                    ),
                )
            ) for o, t in votetimes
        ]

        return reply


class VoteSummaryResource(RedingResource):

    @marshal_with(user_object_resource_fields)
    def get(self, object_id, user_id):
        args = self.parser.parse_args()

        vote = self.redis.zscore(
            get_user_object_key_name(
                object_id=object_id,
                **args
            ),
            user_id,
        )

        when_ts = self.redis.zscore(
            get_user_key_name(
                user_id=user_id,
                **args
            ),
            object_id,
        )

        if not (vote and when_ts):
            m = "No vote on {object_id} by {user_id}.".format(
                object_id=object_id,
                user_id=user_id
            )
            abort(404, message=m)

        return get_user_object_reply(
            object_id=object_id,
            user_id=user_id,
            vote=vote,
            when=datetime.fromtimestamp(
                when_ts,
            ),
        )

    def post(self, object_id, user_id):
        return self.put(object_id, user_id)

    @marshal_with(user_object_resource_fields)
    def put(self, object_id, user_id):
        add_vote_arg(self.parser, required=True)
        args = self.parser.parse_args()

        next_vote = args['vote']

        self._perform_correction(object_id, user_id, next_vote, args)

        self.redis.zadd(
            get_user_object_key_name(
                object_id=object_id,
                **args
            ),
            next_vote,
            user_id,
        )

        self.redis.zadd(
            get_user_key_name(
                user_id=user_id,
                **args
            ),
            time(),
            object_id,
        )

        return get_user_object_reply(
            object_id=object_id,
            user_id=user_id,
            vote=self.redis.zscore(
                get_user_object_key_name(
                    object_id=object_id,
                    **args
                ),
                user_id,
            ),
            when=datetime.fromtimestamp(
                self.redis.zscore(
                    get_user_key_name(
                        user_id=user_id,
                        **args
                    ),
                    object_id,
                ),
            )
        )

    def delete(self, object_id, user_id):
        args = self.parser.parse_args()

        next_vote = 0
        self._perform_correction(object_id, user_id, next_vote, args)

        self.redis.zrem(
            get_user_key_name(
                user_id=user_id,
                **args
            ),
            object_id,
        )

        self.redis.zrem(
            get_user_object_key_name(
                object_id=object_id,
                **args
            ),
            user_id,
        )

        return '', 204

    def _perform_correction(self, object_id, user_id, next_vote, args):
        prev_vote = self.redis.zscore(
            get_user_object_key_name(
                object_id=object_id,
                **args
            ),
            user_id,
        )

        if not prev_vote:
            prev_vote = 0

        correction = next_vote - prev_vote

        # perform vote correction in `all apps` zset
        if correction:
            self.redis.zincrby(
                get_object_key_name(**args),
                object_id,
                correction,
            )

        amount = self.redis.zscore(
            get_object_key_name(**args),
            object_id,
        )

        if not amount and amount == 0:
            self.redis.zrem(
                get_object_key_name(**args),
                object_id,
            )

__all__ = (
    'VotedSummaryResource',
    'VotedListResource',
    'VotingUserListResource',
    'VoteSummaryResource',
    'UserSummaryResource',
)
