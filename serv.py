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

define("port", default=8888, help="run on the given port", type=int)

robot_config = [maestro.load_config_file("ArmL.json"), maestro.load_config_file("ArmR.json")]


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler), (r"/ws", WsHandler)]
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
        logging.info("Serving main.html")
        self.render("main.html", messages=WsHandler.cache)


class WsHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        logging.debug("WsHandler.open():}")
        WsHandler.waiters.add(self)
        try:
            logging.debug("Attempting to send initialization data over WS")
            # self.write_message(tornado.escape.json_encode("Sending initial config"))
            self.write_message(tornado.escape.json_encode(robot_config))
        except:
            logging.error("Could not send initializaiton data over WS")
        
    def on_close(self):
        logging.info("WsHandler.on_close(): {}}".format(self))
        WsHandler.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        logging.info("WsHandler.update_cache: chat: {}".format(chat))
        # cls.cache.append(chat)
        # if len(cls.cache) > cls.cache_size:
        #     cls.cache = cls.cache[-cls.cache_size :]

    @classmethod
    def send_updates(cls, chat):
        logging.info("WsHandler.sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except tornado.websocket.WebSocketClosedError:
                logging.warning("Websocket already closed")
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        try:
            parsed = tornado.escape.json_decode(message)
            chat = {"id": str(uuid.uuid4()), "body": tornado.escape.json_encode(parsed)}
        
        except Exception as e:
            # cannot decode
            error_msg = {'exception': "{}".format(e)}
            chat = {"id": str(uuid.uuid4()), "body":  tornado.escape.json_encode(error_msg)}

        WsHandler.update_cache(chat)
        WsHandler.send_updates(chat)

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()