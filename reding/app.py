from flask import Flask
from flask.ext import restful

from reding.settings import DAEMON_CONFIG
from reding.resources import VotedListResource,\
    VotingUserListResource, VotedSummaryResource, UserSummaryResource, VoteSummaryResource

app = Flask(__name__)
api = restful.Api(app)

api.add_resource(VotedListResource, '/objects/')
api.add_resource(VotingUserListResource, '/objects/<string:object_id>/users/')
api.add_resource(VotedSummaryResource, '/objects/<string:object_id>/')
api.add_resource(UserSummaryResource, '/users/<string:user_id>/')
api.add_resource(
    VoteSummaryResource,
    '/objects/<string:object_id>/users/<string:user_id>/'
)

__all__ = (app,)
