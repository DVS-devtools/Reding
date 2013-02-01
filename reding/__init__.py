from flask import Flask
from flask.ext import restful

from reding.settings import DAEMON_CONFIG
from reding.resources import ObjectList, ObjectUsers, Object, UserList, UserObject

app = Flask(__name__)
api = restful.Api(app)

api.add_resource(ObjectList, '/objects/')
api.add_resource(ObjectUsers, '/objects/<string:object_id>/users/')
api.add_resource(Object, '/objects/<string:object_id>/')
api.add_resource(UserList, '/users/<string:user_id>/')
api.add_resource(
    UserObject,
    '/objects/<string:object_id>/users/<string:user_id>/'
)

if __name__ == '__main__':
    #app.run(debug=True)
    from cherrypy import wsgiserver

    w = wsgiserver.WSGIPathInfoDispatcher({'/': app.wsgi_app})
    server = wsgiserver.CherryPyWSGIServer(
        bind_addr=(
            DAEMON_CONFIG['host'],
            DAEMON_CONFIG['port']
        ),
        wsgi_app=w,
    )

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
