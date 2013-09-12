from reding.managers import ObjectSubjectsManager, SubjectObjectsManager, ObjectsManager
from reding.settings import KEY_CONFIG
from reding.settings import PAGINATION_DEFAULT_OFFSET as OFFSET
from reding.settings import PAGINATION_DEFAULT_SIZE as SIZE

from flask.ext.restful import reqparse, fields, marshal_with, abort
from flask.ext import restful

from time import time


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

        amounts = ObjectsManager(**args).scoredrange(
            offset=args['offset'],
            size=args['size'],
            reverse=args['sort'] == '-',
        )

        reply = []
        osmanager = ObjectSubjectsManager(**args)
        for object_id, amount in amounts:
            votes_no = osmanager.count(object_id=object_id)
            if votes_no:  # skipping objects with no votes
                reply.append(
                    dict(
                        votes_no=votes_no,
                        average=amount / votes_no,
                        amount=amount,
                        object_id=object_id,
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

        return ObjectsManager(**args).filtered(
            objects=args['object_id'],
            now=int(time()),
            reverse=args['sort'] == '-',
        )


class VotedSummaryResource(RedingResource):
    @marshal_with(object_resource_fields)
    def get(self, object_id):
        add_vote_arg(self.parser)
        args = self.parser.parse_args()

        vote = args['vote']

        amount = ObjectsManager(**args).score(object_id=object_id) or 0

        votes_no = ObjectSubjectsManager(**args).count(
            object_id=object_id,
            min_vote=vote or '-inf',
            max_vote=vote or '+inf',
        )

        if not votes_no:
            average = 0
            amount = 0
        elif vote:
            average = vote
            amount = vote * votes_no
        else:
            average = amount / votes_no

        return (
            dict(
                votes_no=votes_no,
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

        votes = ObjectSubjectsManager(**args).scoredrange(
            object_id=object_id,
            offset=args['offset'],
            size=args['size'],
            min_vote=args['vote'] or '-inf',
            max_vote=args['vote'] or '+inf',
            reverse=args['sort'] == '-',
        )
        somanager = SubjectObjectsManager(**args)
        reply = [
            get_user_object_reply(
                object_id=object_id,
                user_id=user_id,
                vote=vote,
                when=somanager.score(user_id=user_id, object_id=object_id),
            ) for user_id, vote in votes
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

        somanager = SubjectObjectsManager(**args)
        osmanager = ObjectSubjectsManager(**args)

        votetimes = somanager.scoredrange(
            user_id=user_id,
            offset=args['offset'],
            size=args['size'],
            reverse=args['sort'] == '-',
        )
        reply = [
            get_user_object_reply(
                object_id=object_id,
                user_id=user_id,
                vote=osmanager.score(object_id=object_id, user_id=user_id),
                when=somanager.score(user_id=user_id, object_id=object_id),
            ) for object_id, t in votetimes
        ]

        return reply


class VoteSummaryResource(RedingResource):
    @marshal_with(user_object_resource_fields)
    def get(self, object_id, user_id):
        args = self.parser.parse_args()

        vote = ObjectSubjectsManager(**args).score(object_id=object_id, user_id=user_id)
        when = SubjectObjectsManager(**args).score(user_id=user_id, object_id=object_id)

        if not (vote and when):
            message = "No vote on {object_id} by {user_id}.".format(
                object_id=object_id,
                user_id=user_id
            )
            abort(404, message=message)

        return get_user_object_reply(
            object_id=object_id,
            user_id=user_id,
            vote=vote,
            when=when,
        )

    def post(self, object_id, user_id):
        return self.put(object_id, user_id)

    @marshal_with(user_object_resource_fields)
    def put(self, object_id, user_id):
        add_vote_arg(self.parser, required=True)
        args = self.parser.parse_args()

        self._perform_correction(object_id, user_id, args['vote'], args)
        ObjectSubjectsManager(**args).create(object_id=object_id, user_id=user_id, vote=args['vote'])
        SubjectObjectsManager(**args).create(user_id=user_id, object_id=object_id, ts=time())

        return get_user_object_reply(
            object_id=object_id,
            user_id=user_id,
            vote=ObjectSubjectsManager(**args).score(object_id=object_id, user_id=user_id),
            when=SubjectObjectsManager(**args).score(user_id=user_id, object_id=object_id),
        )

    def delete(self, object_id, user_id):
        args = self.parser.parse_args()

        self._perform_correction(object_id, user_id, 0, args)
        SubjectObjectsManager(**args).remove(user_id=user_id, object_id=object_id)
        ObjectSubjectsManager(**args).remove(object_id=object_id, user_id=user_id)

        return '', 204

    def _perform_correction(self, object_id, user_id, next_vote, args):
        prev_vote = ObjectSubjectsManager(**args).score(object_id=object_id, user_id=user_id) or 0
        correction = next_vote - prev_vote
        omanager = ObjectsManager(**args)
        omanager.incrby(object_id=object_id, delta=correction)
        amount = omanager.score(object_id=object_id)

        if amount == 0:
            omanager.remove(object_id=object_id)

__all__ = (
    'VotedSummaryResource',
    'VotedListResource',
    'VotingUserListResource',
    'VoteSummaryResource',
    'UserSummaryResource',
)
