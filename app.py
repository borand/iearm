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
"""Simplified chat demo for websockets.

Authentication, error handling, etc are left as an exercise for the reader :)
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import json

import maestro

from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)

arm_l = maestro.Controller('/dev/ttyACM0')
pwm_vector = {"target_pwm_l": [], "target_pwm_r": []}


class Arms():

    def __init__(self):
        arm_l = maestro.Controller('/dev/ttyACM0')
        arm_r = maestro.Controller('/dev/ttyACM2')

    def process_msg(self, msg):
        pass


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler), (r"/chatsocket", ChatSocketHandler)]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", messages=ChatSocketHandler.cache)


class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        ChatSocketHandler.waiters.add(self)

    def on_close(self):
        ChatSocketHandler.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)

        if "button" in message:
            parsed = tornado.escape.json_decode(message)
            if "Save Frame" in parsed['cmd']:
                pwm_vector['target_pwm_l'].append(parsed['body']['target_pwm_l'])
                pwm_vector['target_pwm_r'].append(parsed['body']['target_pwm_r'])
                print(pwm_vector)

            if "Play Sequence" in parsed['cmd']:
                arm_l.run_sequency(pwm_vector['target_pwm_l'])

            if "Reset Sequence" in parsed['cmd']:
                pwm_vector['target_pwm_l'] = []
                pwm_vector['target_pwm_r'] = []

            if "Save to file" in parsed['cmd']:
                filename = 'armlogic_sequency.json'
                fid = open(filename, 'w')
                fid.write(json.dumps(pwm_vector))

            if "Load to file" in parsed['cmd']:
                filename = 'armlogic_sequency.json'
                fid = open(filename, 'r')
                from_file = json.loads(fid.read())
                fid.close()
                pwm_vector['target_pwm_l'] = from_file['target_pwm_l']
                pwm_vector['target_pwm_r'] = from_file['target_pwm_r']



        elif "cmd" in message:
            parsed = tornado.escape.json_decode(message)

            chan = int(parsed['id'][1])
            pwm = int(parsed["body"])
            if "L" in parsed['id'][0]:
                logging.info("moving left arm {}".format(int(parsed["body"])))
                arm_l.set_target(chan, pwm)
            if "R" in parsed['id'][0]:
                logging.info("moving right arm {}".format(int(parsed["body"])))

        else:
            # parsed = tornado.escape.json_decode(message)
            # chat = {"id": str(uuid.uuid4()), "body": parsed["body"]}
            # chat["html"] = tornado.escape.to_basestring(
            #     self.render_string("message.html", message=chat)
            # )

            # ChatSocketHandler.update_cache(chat)
            ChatSocketHandler.send_updates(chat)


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
