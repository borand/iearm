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
import os
import glob
import uuid
import json

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18,GPIO.OUT)
    GPIO.setup(23,GPIO.OUT)
    GPIO.setup(24, GPIO.OUT)
except:
    pass

GPIO.output(18, GPIO.HIGH)
GPIO.output(23, GPIO.HIGH)
GPIO.output(24, GPIO.HIGH)

import maestro

from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)

arm_l = maestro.Controller('/dev/ttyACM0',config_file="ArmR.json")
arm_r = maestro.Controller('/dev/ttyACM2',config_file="ArmL.json")
pwm_vector = {"target_pwm_l": [], "target_pwm_r": []}

def update_positions():
    try:
        msg['pwmvalL'].append(arm_l.get_all_positions())
        msg['pwmvalR'].append(arm_r.get_all_positions())
    except:
        cmd = 'updatePosition';
        # param = {'pwmvalL': arm_l.get_all_positions(),
        #          'pwmvalR': arm_r.get_all_positions()}
        param = {'pwmvalL': arm_l.config['target_position'],
                 'pwmvalR': arm_r.config['target_position']}
        msg = {"cmd": cmd, "param": param}
    return msg


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler), 
        (r"/ws", ChatSocketHandler),
        (r"/api/(\w+)/(.*)", ApiHandler),
        ]
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
        seq_files = glob.glob("*.seq")
        self.render("index.html", seq_files=seq_files)

class ApiHandler(tornado.web.RequestHandler):

    def get(self, *arg):
        
        try:
            cmd_args = json.loads(arg[1])

            if "set_speed" in arg[0]:
                for (chan, val) in enumerate(cmd_args):
                    print("chan:{}, val:{}".format(chan, val))
                    arm_l.set_speed(chan, val)
                    arm_r.set_speed(chan, val)
                ret_msg = 'done'
        except:
            ret_msg = 'error'
        self.write(ret_msg)

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


class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        ChatSocketHandler.waiters.add(self)
        msg = update_positions()
        ChatSocketHandler.send_updates(tornado.escape.json_encode(msg))

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
            if "Save" in parsed['cmd']:
                pwm_vector['target_pwm_l'].append(arm_l.get_all_positions())
                pwm_vector['target_pwm_r'].append(arm_r.get_all_positions())
                msg = update_positions()
                ChatSocketHandler.send_updates(tornado.escape.json_encode(msg))
                print(pwm_vector)

            if "led" in parsed['cmd']:
                GPIO.output(18, not GPIO.input(18))
                GPIO.output(23, GPIO.LOW)
                GPIO.output(24, GPIO.LOW)


            if "Update" in parsed['cmd']:
                print()
                l = parsed['body']['target_pwm_l']
                l.append(arm_l.config['last_position'][5])
                arm_l.set_target_vector(l)

                r = parsed['body']['target_pwm_r']
                r.append(arm_r.config['last_position'][5])
                arm_r.set_target_vector(r)


            if "Play" in parsed['cmd']:
                #arm_l.run_sequency(pwm_vector['target_pwm_l'])
                #arm_r.run_sequency(pwm_vector['target_pwm_r'])
                print(pwm_vector)
                for (l,r) in zip(pwm_vector['target_pwm_l'], pwm_vector['target_pwm_r']):
                    arm_l.set_target_vector(l, match_speed=1, wait=False)
                    arm_r.set_target_vector(r, match_speed=1, wait=True)
                    arm_l.set_speed_vector(arm_l.config['last_speed'])
                    arm_r.set_speed_vector(arm_r.config['last_speed'])
                msg = update_positions()
                ChatSocketHandler.send_updates(tornado.escape.json_encode(msg))

            if "Reset Sequence" in parsed['cmd']:
                pwm_vector['target_pwm_l'] = []
                pwm_vector['target_pwm_r'] = []

            if "Save as" in parsed['cmd']:
                filename = parsed['param']
                filename, file_extension = os.path.splitext(filename)
                if ".seq" not in file_extension:
                    filename = filename + ".seq"

                fid = open(filename, 'w')
                fid.write(json.dumps(pwm_vector))

            if "Delete Sequence" in parsed['cmd']:
                filename = parsed['param']
                os.remove(filename)

            if "Home" in parsed['cmd']:
                arm_l.go_home()
                arm_r.go_home()
                msg = update_positions()
                ChatSocketHandler.send_updates(tornado.escape.json_encode(msg))

            if "Load file" in parsed['cmd']:
                filename = parsed['param']
                fid = open(filename, 'r')
                from_file = json.loads(fid.read())
                fid.close()
                logging.info("loaded file {}".format(filename))
                pwm_vector['target_pwm_l'] = from_file['target_pwm_l']
                pwm_vector['target_pwm_r'] = from_file['target_pwm_r']

            if "Set Home" in parsed['cmd']:
                arm_l.config['home'] = arm_l.get_all_positions()
                arm_r.config['home'] = arm_r.get_all_positions()
                print(arm_l.config['home'])
                print(arm_r.config['home'])

        elif "cmd" in message:
            parsed = tornado.escape.json_decode(message)

            chan = int(parsed['id'][1])
            pwm = int(parsed["body"])
            if "L" in parsed['id'][0]:
                logging.info("moving left arm {}".format(int(parsed["body"])))
                arm_l.set_target(chan, pwm)
            if "R" in parsed['id'][0]:
                logging.info("moving right arm {}".format(int(parsed["body"])))
                arm_r.set_target(chan, pwm)
            msg = update_positions()
            ChatSocketHandler.send_updates(tornado.escape.json_encode(msg))

        else:
            # parsed = tornado.escape.json_decode(message)
            # chat = {"id": str(uuid.uuid4()), "body": parsed["body"]}
            # chat["html"] = tornado.escape.to_basestring(
            #     self.render_string("message.html", message=chat)
            # )

            # ChatSocketHandler.update_cache(chat)
            #ChatSocketHandler.send_updates(chat)
            pass



def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port, address='0.0.0.0')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

