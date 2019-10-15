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

var MyData = {};

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
            updater.wsMessage(event.data);
        }

    },

    stop: function() {
        updater.socket.onclose = function(event){
            console.log("Websocket closed");
            updater.socket.close()
        }
    },

    wsMessage: function(message) {
        // console.log(message)
        last_msg = message;

        try{
            var data = JSON.parse(message);
            var obj_keys = Object.keys(data[0]);
            var tab_keys = ["min", "max"]
            // debugger
            for (i = 0; i < obj_keys.length; i++) {
                
                if (tab_keys.includes(obj_keys[i]))
                {
                    // console.log(obj_keys[i]);
                    var row_data = obj_keys[i]
                    row_data = row_data.concat(data[0][obj_keys[i]]);
                    console.log(row_data)
                    //MyData.T.row.add(row_data).draw(false);
                }
            }   

        } catch(err) {console.log("Failed ws JSON decode: " + err)}

        
        
        // for (i = 0; i < obj_keys.length; i++) {
        //     console.log(obj_keys[i]);
        //     if ([data[0][obj_keys[i]] != 'cal'){
            
        //         T.row.add([
        //             [data[0][obj_keys[i]]
        //         ]
        //         ).draw( false );
        //   }
        //}

    }
};


$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};
    var last_msg = {};
    MyData.T = $('#myTable').DataTable({
        "paging":   false,
        "ordering": false,
        "info":     false,
        "dom": '<"top"><"bottom"><"clear">'
    });

    var joyconfig = {
        xAxis: true,
        yAxis: true,
		moveEvent: function(pos) {
            console.log('joystick: (x,y) = (' + pos.x + ', ' + pos.y + ')')
        },
		endEvent: function(pos) { console.log('joystick: (x,y) = (' + pos.x + ', ' + pos.y + ')') }
    };

    MyData.J1 = $('#j-1').joystick(joyconfig);
    
    updater.start();
});