#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.




import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

import maestro
import time

sp  = maestro.Controller()
sp2 = maestro.Controller('/dev/ttyACM2')

dev = {"light": 0}

trajectory2 = [
    [[1500, 1150, 1275, 1000],  0.5],
    [[2300, 1850, 1275, 1000], 0.5],
    [[2300, 1950, 1275, 1000], 0.5],
    [[2300, 1950, 1275, 1800], 0.5],
    [[2300, 1150, 1975, 1800], 0.5],
    [[1100, 1150, 1975, 1800], 0.5],
    [[950, 1950, 1175, 1800], 0.5],
    [[950, 1950, 1175, 1000], 0.5],
    [[1500, 1150, 1275, 1000],  0.5],
    ]

trajectory = [
    [[1500, 1692, 1773, 1228, 904], 2],
    [[1477, 1185, 864, 1228, 904], 1],
    [[1477, 1185, 864, 1228, 1671], 1],
    [[1477, 2100, 864, 1228, 1671], 1],
    [[802, 826, 1675, 1228, 1671], 1],
    [[802, 826, 1675, 1228, 904], 1],
    [[802, 1692, 1675, 1228, 904], 1],
    [[1500, 1692, 1773, 1228, 904], 1]
]


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class IdnHandler(tornado.web.RequestHandler):
    def get(self):
        out = "not implemented"
        self.write("{}".format(out))

class CmdHandler(tornado.web.RequestHandler):
    def get(self, cmd):
        out = "command not implementd"
        self.write("{}".format(out))

class ApiHandler(tornado.web.RequestHandler):

    def get(self, *arg):
        print("get")
        self.write('{"is_active": "true"}')

    def put(self, *arg, **kwargs):
        print("put")
        self.write('{"is_active": "false"}')

    def post(self, *arg, **kwargs):
        print("post ----------------------------------------------")
        print(self.request)
        body = self.request.body.decode("utf-8")
        try:
            out = json.loads(body)
            dev[out["dev"]] = out["active"]
        except:
            out = 'could not decode'
        print("body = {}, type = {}, json = {}".format(body, type(body), out))

        self.write('{"is_active": "true"}')

class ApiSetPos(tornado.web.RequestHandler):

    def get(self, chan, pos, *arg):
        print("ApiSetPos get chan{}-{}, pos{}-{}".format(chan, type(chan), pos, type(pos)))

        start_time = time.time()
        try:
            sp.set_target(int(chan), int(pos))
            success = 1
        except:
            success = 0
        end_time = time.time()
        out = {"cmd": chan, "pos": pos, "cmd": "set_target", "success" : success, "etime": start_time - end_time}
        self.write(json.dumps(out))

class ApiRunTrajectory(tornado.web.RequestHandler):

    def get(self, *arg):
        # print("ApiSetPos get chan{}-{}, pos{}-{}".format(arg))
        starttime = time.time()

        sp.run_trajectory(trajectory)
        time.sleep(1);
        sp2.run_trajectory(trajectory2)

        endtime = time.time()
        self.write('cmd: {}, time: {}'.format("run_trajectory", endtime-starttime))

def main():
    tornado.options.parse_command_line()
    settings = {
        'debug': True,
        # other stuff
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/idn", IdnHandler),
        (r"/cmd/(.*)", CmdHandler),
        (r"/api/", ApiHandler),
        (r"/api/setpos/([0-5])/pos/(\d+)", ApiSetPos),
        (r"/api/run_trajectory", ApiRunTrajectory),
    ], debug=True, autoreload=True)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

x = {"username": "andrzej", "args": [], "name": "loger_test", "level": "info", "line_no": 1, "traceback": 0, "filename": "<stdin>", "time": "2017-12-01T02:53:41.392427", "msg": "I am a message", "funcname": "<module>", "hostname": "deepspace9"}

if __name__ == "__main__":
    main()