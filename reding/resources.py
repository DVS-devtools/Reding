from reding.managers import ObjectSubjectsManager, SubjectObjectsManager, ObjectsManager
from reding.settings import KEY_CONFIG
from reding.settings import PAGINATION_DEFAULT_OFFSET as OFFSET
from reding.settings import PAGINATION_DEFAULT_SIZE as SIZE

from flask.ext.restful import reqparse, fields, marshal_with, abort
from flask.ext import restful

from time import time
from six import text_type


def get_user_object_reply(object_id, user_id, vote, when, review):
    return {
        'object_id': object_id,
        'user_id': user_id,
        'vote': vote,
        'when': when,
        'review': review
    }


object_resource_fields = {
    'votes_no': fields.Integer,
    'amount': fields.Integer,
    'average': fields.Float,
    'object_id': fields.String,
}

user_object_resource_fields = {
    'vote': fields.Integer,
    'review': fields.Raw,
    'object_id': fields.String,
    'user_id': fields.String,
    'when': fields.DateTime
}


class RedingResource(restful.Resource):
    parser_cls = reqparse.RequestParser

    def __init__(self):
        super(RedingResource, self).__init__()
        self.parser = self.parser_cls()
        self.configure()

    def configure(self):
        for key in KEY_CONFIG:
            self.parser.add_argument(key, type=str)


class VotedListResource(RedingResource):
    def configure(self):
        super(VotedListResource, self).configure()
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
    def configure(self):
        super(VotedSummaryResource, self).configure()
        self.parser.add_argument('vote', type=int, default=0)

    @marshal_with(object_resource_fields)
    def get(self, object_id):
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
    def configure(self):
        super(VotingUserListResource, self).configure()
        self.parser.add_argument('sort', type=str, default='+')
        self.parser.add_argument('offset', type=int, default=OFFSET)
        self.parser.add_argument('size', type=int, default=SIZE)
        self.parser.add_argument('vote', type=int, default=0)

    @marshal_with(user_object_resource_fields)
    def get(self, object_id):
        args = self.parser.parse_args()

        osmanager = ObjectSubjectsManager(**args)
        somanager = SubjectObjectsManager(**args)

        votes = osmanager.scoredrange(
            object_id=object_id,
            offset=args['offset'],
            size=args['size'],
            min_vote=args['vote'] or '-inf',
            max_vote=args['vote'] or '+inf',
            reverse=args['sort'] == '-',
        )

        if not votes:
            return []

        reviews = osmanager.reviews(object_id, *[user_id for user_id, _ in votes])

        reply = [
            get_user_object_reply(
                object_id=object_id,
                user_id=user_id,
                vote=vote,
                when=somanager.score(user_id=user_id, object_id=object_id),
                review=reviews[user_id],
            ) for user_id, vote in votes
        ]
        return reply


class UserSummaryResource(RedingResource):
    def configure(self):
        super(UserSummaryResource, self).configure()
        self.parser.add_argument('sort', type=str, default='+')
        self.parser.add_argument('offset', type=int, default=OFFSET)
        self.parser.add_argument('size', type=int, default=SIZE)

    @marshal_with(user_object_resource_fields)
    def get(self, user_id):
        args = self.parser.parse_args()

        osmanager = ObjectSubjectsManager(**args)
        somanager = SubjectObjectsManager(**args)

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
                review=osmanager.review(object_id=object_id, user_id=user_id),
                when=when,
            ) for object_id, when in votetimes
        ]

        return reply


class VoteSummaryResource(RedingResource):
    @marshal_with(user_object_resource_fields)
    def get(self, object_id, user_id):
        args = self.parser.parse_args()

        osmanager = ObjectSubjectsManager(**args)
        somanager = SubjectObjectsManager(**args)

        vote = osmanager.score(object_id=object_id, user_id=user_id)
        when = somanager.score(user_id=user_id, object_id=object_id)

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
            review=osmanager.review(object_id=object_id, user_id=user_id),
        )

    def post(self, object_id, user_id):
        return self.put(object_id, user_id)

    @marshal_with(user_object_resource_fields)
    def put(self, object_id, user_id):
        self.parser.add_argument('vote', type=int, required=True)
        self.parser.add_argument('review', type=text_type)
        args = self.parser.parse_args()

        osmanager = ObjectSubjectsManager(**args)
        somanager = SubjectObjectsManager(**args)

        self._perform_correction(object_id, user_id, args['vote'], args)
        osmanager.create(object_id=object_id, user_id=user_id, vote=args['vote'], review=args['review'])
        somanager.create(user_id=user_id, object_id=object_id, timestamp=time())

        return get_user_object_reply(
            object_id=object_id,
            user_id=user_id,
            vote=osmanager.score(object_id=object_id, user_id=user_id),
            when=somanager.score(user_id=user_id, object_id=object_id),
            review=osmanager.review(object_id=object_id, user_id=user_id),
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
