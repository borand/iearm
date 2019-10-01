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

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#messageform").on("submit", function() {
        newMessage($(this));
        return false;
    });
    $("#messageform").on("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });
    $("#message").select();
    updater.start();

    $(".slider").change(function () {
        var element_id = $(this).attr("id").substring(3, 5)
        var elemtn_val = $(this).val();
        console.log(element_id + "  val:" + elemtn_val);
        $("#pwmval"+element_id).val(elemtn_val);
        var data = {"id" : element_id, "body" : elemtn_val, "cmd" : "move"};
        updater.socket.send(JSON.stringify(data));
    });

    $(".cmd_button").click(function () {
        var target_pwm_l = [];
        var target_pwm_r = [];
        $(".target_pwm").each(function () {
            if ($(this).attr("id")[6] === "L"){
                target_pwm_l.push(parseInt($(this).val()))
            }
            else if($(this).attr("id")[6] === "R"){
                target_pwm_r.push(parseInt($(this).val()))
            }

        });
        console.log("target_pwm_l = " + target_pwm_l + ",   target_pwm_r" + target_pwm_r);

        var data = {"id" : "button", "body" : {"target_pwm_l": target_pwm_l,  "target_pwm_r" : target_pwm_r}, "cmd" : $(this).val()};
        updater.socket.send(JSON.stringify(data));


    });


    $('#throttle-stick').joystick({
		//xAxis: false,
		moveEvent: function(pos) { console.log('throttle:' + pos.y) },
		endEvent: function(pos) { console.log('throttle:' + pos.y) }
	});
	$('#yaw-stick').joystick({
		yAxis: false,
		xSnap: true,
		moveEvent: function(pos) { console.log('yaw:' + pos.x) },
		endEvent: function(pos) { console.log('yaw:' + pos.x) }
    });
    $('#r-stick').joystick({
		yAxis: false,
		xSnap: true,
		moveEvent: function(pos) { console.log('yaw:' + pos.x) },
		endEvent: function(pos) { console.log('yaw:' + pos.x) }
    });
    
    
	
	$('#throttle-stick').joystick('value', 0.5, 0);
	$('#yaw-stick').joystick('value', 1, 0.5);
	
	var y = $('#throttle-stick').joystick('value').y;
	console.log(y);
});

function newMessage(form) {
    var message = form.formToDict();
    updater.socket.send(JSON.stringify(message));
    form.find("input[type=text]").val("").select();
}

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/chatsocket";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            updater.showMessage(JSON.parse(event.data));
        }
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        //var node = $(message.html);
        //node.hide();
        //$("#inbox").append(node);
        $("#inbox").text("last msg: " + message.html);
        //node.slideDown();
    }
};