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

    $("#controlform").on("submit", function() {
        newMessage($(this));
        return false;
    });

    $("#controlform").on("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });
    
    $('#servo1').joystick({
		//xAxis: false,
		moveEvent: function(pos) {
            console.log('joystick: (x,y) = (' + pos.x + ', ' + pos.y + ')')
        },
		endEvent: function(pos) { console.log('joystick: (x,y) = (' + pos.x + ', ' + pos.y + ')') }
    });
    
    updater.start();
});

function newMessage(form) {
    //var message = form.formToDict();
    //console.log("Sending: " + JSON.stringify(message))
    var  form = $("#controlform").serializeArray();
    var json = {};
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    updater.socket.send(JSON.stringify(json));
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
        console.log("Connecting to websocket at URL: " + url)
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            //console.log(event)
            updater.showMessage(event.data);
        }

    },

    stop: function() {
        updater.socket.onclose = function(event){
            console.log("Websocket closed");
            updater.socket.close()
        }
    },

    showMessage: function(message) {
        console.log(message)
        //JSON.parse(message.data)
    }
};