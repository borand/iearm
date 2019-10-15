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

    updater.start();

    $(".arm_param").change(function(){
        var element_id = $(this).attr("id");
        var elemtn_val = parseInt($(this).val());
        var json_val = JSON.stringify([elemtn_val, elemtn_val, elemtn_val, elemtn_val, elemtn_val, elemtn_val])
        var api_url = "api/"+ element_id + "/"+json_val;
        console.log("id: " + element_id + "  val: " + elemtn_val)
        $.get( "api/"+element_id+"/"+json_val, function( data ) {
            console.log(data);
        });
    })

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

    //========================================================================================
    $('#arm_forearm_l').joystick({
		//xAxis: false,
		moveEvent: function(pos) {
            var data = {"id" : 'L2', "body" : 500 + Math.round(2000*pos.x), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id" : 'L1', "body" : 500 + Math.round(2000*pos.y), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
        },
		endEvent: function(pos) { console.log('throttle:' + pos.y) }
	});
	$('#wrist_forearm_l').joystick({
		//yAxis: false,
        //xSnap: true,        
		moveEvent: function(pos) { 
            var data = {"id" : 'L4', "body" : 500 + Math.round(2000*(pos.x)), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id" : 'L3', "body" : 500 + Math.round(2000*(pos.y)), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos);
        },
		endEvent: function(pos) { console.log(pos) }
    });
    $('#base_l').joystick({
		xAxis: false,
		ySnap: true,
		moveEvent: function(pos) { 
            var data = {"id" : 'L5', "body" : 2455 - Math.round(2000*pos.y), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos.x) },
		endEvent: function(pos) { console.log('yaw:' + pos.x) }
    });
    //========================================================================================
    $('#arm_forearm_r').joystick({
		//xAxis: false,
		moveEvent: function(pos) {
            var data = {"id" : 'R2', "body" : 500 + Math.round(2000*(pos.x)), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id" : 'R1', "body" : 500 + Math.round(2000*(1-pos.y)), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
        },
		endEvent: function(pos) { console.log('throttle:' + pos.y) }
	});
	$('#wrist_forearm_r').joystick({
		//yAxis: false,
        //xSnap: true,        
		moveEvent: function(pos) { 
            var data = {"id" : 'R4', "body" : 500 + Math.round(2000*(1-pos.x)), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            var data = {"id" : 'R3', "body" : 1500 + Math.round(2000*(1-pos.y)), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos);
        },
		endEvent: function(pos) { console.log(pos) }
    });
    $('#base_r').joystick({
		xAxis: false,
		ySnap: true,
		moveEvent: function(pos) { 
            var data = {"id" : 'R5', "body" : 1900 + Math.round(500*pos.y), "cmd" : "move"};
            updater.socket.send(JSON.stringify(data));
            console.log('yaw:' + pos.x) },
		endEvent: function(pos) { console.log('yaw:' + pos.x) }
    });

    
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
        var url = "ws://" + location.host + "/ws";
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