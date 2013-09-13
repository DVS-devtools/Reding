Reding
======

[![Build Status](https://secure.travis-ci.org/BuongiornoMIP/Reding.png?branch=master)](https://travis-ci.org/BuongiornoMIP/Reding)
[![Coverage Status](https://coveralls.io/repos/BuongiornoMIP/Reding/badge.png?branch=master)](https://coveralls.io/r/BuongiornoMIP/Reding)
[![PyPi version](https://pypip.in/v/Reding/badge.png)](https://crate.io/packages/Reding/)
[![PyPi downloads](https://pypip.in/d/Reding/badge.png)](https://crate.io/packages/Reding/)

Rating on Redis - REST API on Flask
-----------------------------------
Reding is a *WSGI* Python app made using the amazing Flask web framework, and one of its extension, Flask-RESTful.

On Redis side, it uses the powerful sorted set data type to provide all the functionalities.


Installation:
-------------
```
pip install Reding
```


Some examples:
--------------
Let's start, my Reding is empty, no book has been voted:
```
$ curl -i http://localhost:5000/objects/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 2
Date: Fri, 01 Feb 2013 16:50:47 GMT
Server: mindflayer
```
```json
[]
```

I wanna give a '10' to the amazing 'Core Python Applications Programming' book (ISBN-13: 978-0132678209):
```
$ curl -i -XPUT http://localhost:5000/objects/978-0132678209/users/gsalluzzo/ -d "vote=10"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 110
Date: Fri, 01 Feb 2013 16:57:44 GMT
Server: mindflayer
```
```json
{
    "vote": 10,
    "when": "Fri, 01 Feb 2013 17:57:44 -0000",
    "user_id": "gsalluzzo",
    "object_id": "978-0132678209",
    "review": null
}
```
Ehy hackers, I've just used a PUT call, but yes, I know, it's the first vote, I should use a POST one. Reding maps POST method on the PUT one, so the client does not need to know if it's the first time I'm voting this object.

OK, '10' is too much indeed, let's change it to '9', or the author will get crazy about that:
```
$ curl -i -XPUT http://localhost:5000/objects/978-0132678209/users/gsalluzzo/ -d "vote=9"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 109
Date: Fri, 01 Feb 2013 17:03:16 GMT
Server: mindflayer
```
```json
{
    "vote": 9,
    "when": "Fri, 01 Feb 2013 18:03:16 -0000",
    "user_id": "gsalluzzo",
    "object_id": "978-0132678209",
    "review": null
}
```

Let's see if somebody voted something (my memory is like the gold fish one):
```
$ curl -i http://localhost:5000/objects/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 79
Date: Fri, 01 Feb 2013 17:05:46 GMT
Server: mindflayer
```
```json
[{
    "amount": 9,
    "average": "9.0",
    "object_id": "978-0132678209",
    "votes_no": 1
}]
```

Not expected... ;) Let's enter another vote:
```
$ curl -i -XPUT http://localhost:5000/objects/978-0132678209/users/wchun/ -d "vote=10"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 106
Date: Fri, 01 Feb 2013 17:08:03 GMT
Server: mindflayer
```
```json
{
    "vote": 10,
    "when": "Fri, 01 Feb 2013 18:08:03 -0000",
    "user_id": "wchun",
    "object_id": "978-0132678209",
    "review": null
}
```
The author said '10'! What a surprise! :D

Let's get the voted books again:
```
$ curl -i http://localhost:5000/objects/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 80
Date: Fri, 01 Feb 2013 17:09:42 GMT
Server: mindflayer
```
```json
[{
    "amount": 19,
    "average": "9.5",
    "object_id": "978-0132678209",
    "votes_no": 2
}]
```

There's only a book, what if I only get that one??
```
$ curl -i http://localhost:5000/objects/978-0132678209/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 78
Date: Fri, 01 Feb 2013 17:11:13 GMT
Server: mindflayer
```
```json
{
    "amount": 19,
    "average": "9.5",
    "object_id": "978-0132678209",
    "votes_no": 2
}
```

Or what if I only get my single vote?
```
$ curl -i http://localhost:5000/objects/978-0132678209/users/gsalluzzo/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 109
Date: Fri, 01 Feb 2013 17:12:00 GMT
Server: mindflayer
```
```json
{
    "vote": 9,
    "when": "Fri, 01 Feb 2013 18:03:16 -0000",
    "user_id": "gsalluzzo",
    "object_id": "978-0132678209",
    "review": null
}
```

Let's remove the author's one, he cheated:
```
$ curl -i -XDELETE http://localhost:5000/objects/978-0132678209/users/wchun/
HTTP/1.1 204 NO CONTENT
Content-Type: application/json
Content-Length: 0
Date: Fri, 01 Feb 2013 17:13:45 GMT
Server: mindflayer
```

Let's enter my mom's vote, she does not like Python, she even doesn't know what it is...
```
$ curl -i -XPUT http://localhost:5000/objects/978-0132678209/users/mymom/ -d "vote=3"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 105
Date: Fri, 01 Feb 2013 17:15:38 GMT
Server: mindflayer
```
```json
{
    "vote": 3,
    "when": "Fri, 01 Feb 2013 18:15:38 -0000",
    "user_id": "mymom",
    "object_id": "978-0132678209",
    "review": null
}
```

Let's see the average, it must be decreased:
```
$ curl -i http://localhost:5000/objects/978-0132678209/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 78
Date: Fri, 01 Feb 2013 17:17:09 GMT
Server: mindflayer
```
```json
{
    "amount": 12,
    "average": "6.0",
    "object_id": "978-0132678209",
    "votes_no": 2
}
```

Well, stop programming books...I'm gonna give a '10' to the amazing 'The Lord of the Rings Sketchbook',
but this time let me add a review:
```
$ curl -i -XPUT http://localhost:5000/objects/978-0618640140/users/gsalluzzo/ -d "vote=10&review=the ☃ loves lotr"
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 110
Date: Fri, 01 Feb 2013 17:21:56 GMT
Server: mindflayer
```
```json
{
    "vote": 10,
    "when": "Fri, 01 Feb 2013 18:21:56 -0000",
    "user_id": "gsalluzzo",
    "object_id": "978-0618640140",
    "review": "the ☃ loves lotr"
}
}
```

Let's see the books I voted and what I wrote about them:
```
$ curl -i http://localhost:5000/users/gsalluzzo/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 223
Date: Fri, 01 Feb 2013 17:22:55 GMT
Server: mindflayer
```
```json
[{
    "vote": 9,
    "when": "Fri, 01 Feb 2013 18:03:16 -0000",
    "user_id": "gsalluzzo",
    "object_id": "978-0132678209",
    "review": null
}, {
    "vote": 10,
    "when": "Fri, 01 Feb 2013 18:21:56 -0000",
    "user_id": "gsalluzzo",
    "object_id": "978-0618640140",
    "review": "the ☃ loves lotr"
}]
```

...and again all books voted:
```
$ curl -i http://localhost:5000/objects/
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 161
Date: Fri, 01 Feb 2013 17:23:51 GMT
Server: mindflayer
```
```json
[{
    "amount": 10,
    "average": "10.0",
    "object_id": "978-0618640140",
    "votes_no": 1
}, {
    "amount": 12,
    "average": "6.0",
    "object_id": "978-0132678209",
    "votes_no": 2
}]
```


Filters (on GET's views):
--------
* *vote=* available on "/objects/<<string:object_id>>/" and "/objects/<<string:object_id>>/users/" interfaces.


What's missing:
----------------
* List pagination; DONE!
* List sorting; DONE!
* Any suggestion?


Thanks to:
----------
* **Redis** project at http://redis.io/;
* **Flask** project at http://flask.pocoo.org/;
* **Flask-RESTful** project at https://github.com/twilio/flask-restful/;
* **CherryPy** project at http://cherrypy.org/ - if you wanna try it right now!;
* **Buongiorno S.p.A.** -my company-, letting me open sources to the world.


LICENSE
-------
The MIT License (MIT)

Copyright (c) 2013 Buongiorno S.p.A.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
