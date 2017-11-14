odoo.define('sped_cfe.cfe_sat', function (require) {
"use strict";

var form_widget = require('web.form_widgets');
var core = require('web.core');
var Session = require('web.Session');
var Model = require('web.Model');
var ajax = require('web.ajax');
var _t = core._t;

form_widget.WidgetButton.include({
    on_click: function() {
        var self = this;
        if(this.node.attrs.custom === "enviar_cfe"){
            self.connection = self.connect("http://localhost:5000");
            var session_id = self.session.session_id;
            var options = {};
            var params = {
                'numero_caixa': 1,
                'session_id': session_id,
            };
            var settings = {};
            var url = "http://localhost:5000/hub/v1/consultarsat?session_id=" + session_id;
            $.ajax({
                url: url,
                data: params,
                type: "POST",
                dataType: 'json',
                traditional: true,
                contentType: "application/x-www-form-urlencoded",
                xhrFields: {
                    withCredentials: false
                },
                crossDomain: true
            }).done(function(response) {
                alert(response.funcao + ": " + response.retorno);
                return (new Model('res.users')).call('search_read', [[['id', '=', 1]]]).then(function (result) {
                    alert(result[0].display_name);
                }, function (error) {
                    alert(error);
                });
            }).fail(function (error) {
                alert(error.statusText);
            });
        } else {
            this._super();
        }
    },
    connect: function(url) {
        return new Session(undefined, url, {use_cors: true});
    },
    message : function(name, params, connection, options){
        return connection.rpc(name, params || {}, options);
    }
});
});