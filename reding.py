from flask import Flask
from flask.ext import restful

from settings import DAEMON_CONFIG
from resources import ObjectList, ObjectUsers, Object, UserList, UserObject

app = Flask(__name__)
api = restful.Api(app)

api.add_resource(ObjectList, '/objects/')
api.add_resource(ObjectUsers, '/objects/<string:subject_id>/users/')
api.add_resource(Object, '/objects/<string:subject_id>/')
api.add_resource(UserList, '/users/<string:object_id>/')
api.add_resource(
    UserObject,
    '/objects/<string:subject_id>/users/<string:object_id>/'
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
