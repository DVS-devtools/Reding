__author__ = 'Giorgio Salluzzo <giorgio.salluzzo@gmail.com>'
__version__ = '1.99.1'
__classifiers__ = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
]
__copyright__ = "2013, Buongiorno Spa"
__license__ = """Copyright (C) %s

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.""" % __copyright__

__docformat__ = 'restructuredtext en'

__doc__ = """
:abstract: Rating on Redis - REST API on Flask
:version: %s
:author: %s
:contact: https://github.com/BuongiornoMIP/Reding
:date: 2013-02-01
:copyright: %s
""" % (__version__, __author__, __license__)

if __name__ == '__main__':
    from reding.app import app
    from reding.settings import DAEMON_CONFIG
    # app.run(debug=True, port=5001); import sys; sys.exit()
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
        print('Shutting down Reding...')
    finally:
        server.stop()
        print('Done.')
