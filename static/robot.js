// Copyright 2009 FriendFeed
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

var UI = {
    updatePosition: function (obj) {
        console.log("UI.updatePosition(): " + obj)
        for (let key in obj) {
            let pwm = obj[key];
            // console.log(pwm)
            for (let i = 0; i < pwm.length; i++) {
                // console.log(key + i + "=" + pwm[i])
                $("#" + (key + i)).val(pwm[i])
            }
        }
    },
};

var manualUpdate = function () {
    var target_pwm_l = [];
    var target_pwm_r = [];

    $(".target_pwm").each(function () {
        if ($(this).attr("id")[6] === "L") {
            target_pwm_l.push(parseInt($(this).val()))
        } else if ($(this).attr("id")[6] === "R") {
            target_pwm_r.push(parseInt($(this).val()))
        }

    });
    console.log("target_pwm_l = " + target_pwm_l + ",   target_pwm_r" + target_pwm_r);

    var data = {
        "id": "button",
        "body": {"target_pwm_l": target_pwm_l, "target_pwm_r": target_pwm_r},
        "cmd": $(this).val()
    };
    // updater.socket.send(JSON.stringify(data));
};

$(document).ready(function () {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function () {
    };

    updater.start();

    $(".target_pwm").keyup(function (e) {
        switch (e.which) {
            case 38:
                break;
            case 40:
                break;
            default:
                return
        }
        var target_pwm_l = [];
        var target_pwm_r = [];

        $(".target_pwm").each(function () {
            if ($(this).attr("id")[6] === "L") {
                target_pwm_l.push(parseInt($(this).val()))
            } else if ($(this).attr("id")[6] === "R") {
                target_pwm_r.push(parseInt($(this).val()))
            }

        });
        console.log("target_pwm_l = " + target_pwm_l + ",   target_pwm_r" + target_pwm_r);

        var data = {
            "id": "button",
            "body": {"target_pwm_l": target_pwm_l, "target_pwm_r": target_pwm_r},
            "cmd": "Update"
        };
        updater.socket.send(JSON.stringify(data));
    });

    $(".arm_param").change(function () {
        var element_id = $(this).attr("id");
        var elemtn_val = parseInt($(this).val());
        var json_val = JSON.stringify([elemtn_val, elemtn_val, elemtn_val, elemtn_val, elemtn_val, elemtn_val])
        var api_url = "api/" + element_id + "/" + json_val;
        console.log("id: " + element_id + "  val: " + elemtn_val)
        $.get("api/" + element_id + "/" + json_val, function (data) {
            console.log(data);
        });
    })


    $(".cmd_button").click(function () {
        // Handle buttons
        var data = {"id": "button", "cmd": $(this).val()};
        // Handle button: SAVE AS
        if (data['cmd'] === "Save as") {
            data['param'] = $("#save_filename").val()
            let option_text = data['param'] + ".seq";
            var o = new Option(option_text, option_text);
            /// jquerify the DOM object 'o' so we can use the html method
            $(o).html(option_text);
            $("#load_file").append(o);
        }
        // Handle button: Load and delete files
        if ((data['cmd'] === "Load file") || (data['cmd'] === "Delete Sequence")) {
            data['param'] = $("#load_file").val()
        }
        // Handle button: Load and delete files
        if (data['cmd'] === "Update") {
            var target_pwm_l = [];
            var target_pwm_r = [];

            $(".target_pwm").bind('keyup mouseup', function () {
                var target_pwm_l = [];
                var target_pwm_r = [];

                $(".target_pwm").each(function () {
                    if ($(this).attr("id")[6] === "L") {
                        target_pwm_l.push(parseInt($(this).val()))
                    } else if ($(this).attr("id")[6] === "R") {
                        target_pwm_r.push(parseInt($(this).val()))
                    }

                });
                console.log("target_pwm_l = " + target_pwm_l + ",   target_pwm_r" + target_pwm_r);

                var data = {
                    "id": "button",
                    "body": {"target_pwm_l": target_pwm_l, "target_pwm_r": target_pwm_r},
                    "cmd": $(this).val()
                };
                updater.socket.send(JSON.stringify(data));
            });

            $(".target_pwm").each(function () {
                if ($(this).attr("id")[6] === "L") {
                    target_pwm_l.push(parseInt($(this).val()))
                } else if ($(this).attr("id")[6] === "R") {
                    target_pwm_r.push(parseInt($(this).val()))
                }

            });
            console.log("target_pwm_l = " + target_pwm_l + ",   target_pwm_r" + target_pwm_r);

            var data = {
                "id": "button",
                "body": {"target_pwm_l": target_pwm_l, "target_pwm_r": target_pwm_r},
                "cmd": $(this).val()
            };
            updater.socket.send(JSON.stringify(data));
        }
        console.log(data)
        updater.socket.send(JSON.stringify(data));

    });

    //========================================================================================
    $('#arm_forearm_l').joystick({
        //xAxis: false,
        moveEvent: function (pos) {
            var data = {"id": 'L2', "body": 500 + Math.round(2000 * pos.x), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id": 'L1', "body": 500 + Math.round(2000 * pos.y), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
        },
        endEvent: function (pos) {
            console.log('throttle:' + pos.y)
        }
    });
    $('#wrist_forearm_l').joystick({
        //yAxis: false,
        //xSnap: true,        
        moveEvent: function (pos) {
            var data = {"id": 'L4', "body": 500 + Math.round(2000 * (pos.x)), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id": 'L3', "body": 500 + Math.round(2000 * (pos.y)), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos);
        },
        endEvent: function (pos) {
            console.log(pos)
        }
    });
    $('#base_l').joystick({
        xAxis: false,
        ySnap: true,
        moveEvent: function (pos) {
            var data = {"id": 'L5', "body": 2455 - Math.round(2000 * pos.y), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos.x)
        },
        endEvent: function (pos) {
            console.log('yaw:' + pos.x)
        }
    });
    $('#shoulder_l').joystick({
        xAxis: false,
        ySnap: false,
        moveEvent: function (pos) {
            var data = {"id": 'L0', "body": 500 + Math.round(2000 * pos.y), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos.x)
        },
        endEvent: function (pos) {
            console.log('yaw:' + pos.x)
        }
    });

    //========================================================================================
    $('#arm_forearm_r').joystick({
        //xAxis: false,
        moveEvent: function (pos) {
            var data = {"id": 'R2', "body": 500 + Math.round(2000 * (pos.x)), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id": 'R1', "body": 500 + Math.round(2000 * (1 - pos.y)), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
        },
        endEvent: function (pos) {
            console.log('throttle:' + pos.y)
        }
    });
    $('#wrist_forearm_r').joystick({
        //yAxis: false,
        //xSnap: true,        
        moveEvent: function (pos) {
            var data = {"id": 'R4', "body": 500 + Math.round(2000 * (1 - pos.x)), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id": 'R3', "body": 500 + Math.round(2000 * (1 - pos.y)), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos);
        },
        endEvent: function (pos) {
            console.log(pos)
        }
    });
    $('#shoulder_r').joystick({
        xAxis: false,
        ySnap: false,
        moveEvent: function (pos) {
            var data = {"id": 'R0', "body": 2455 - Math.round(2000 * pos.y), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos.x)
        },
        endEvent: function (pos) {
            console.log('yaw:' + pos.x)
        }
    });
    $('#base_r').joystick({
        xAxis: false,
        ySnap: true,
        moveEvent: function (pos) {
            var data = {"id": 'R5', "body": 1900 + Math.round(500 * pos.y), "cmd": "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos.x)
        },
        endEvent: function (pos) {
            console.log('yaw:' + pos.x)
        }
    });


});

var updater = {
    socket: null,

    start: function () {
        var url = "ws://" + location.host + "/ws";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function (event) {
            updater.showMessage(event.data);
        }
    },

    showMessage: function (event_data) {
        console.log(event_data)
        try {
            let message = JSON.parse(event_data)
            let obj = message;
            let cmd = obj.cmd;
            let param = obj.param;
            UI[cmd](param);
        } catch {
            console.log('could not process incomming message: ' + event_data)
        }
    }
};

