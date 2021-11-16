/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/


odoo.define('l10n_br_pos.devices', function (require) {
    "use strict";
    var devices = require('point_of_sale.devices');
    var core = require('web.core');
    var _t   = core._t;

    var ProxyDeviceSuper = devices.ProxyDevice;

    devices.ProxyDevice = devices.ProxyDevice.extend({
        init: function(parent, options){
            var res = ProxyDeviceSuper.prototype.init.call(this, parent, options);
            // this.customer_display_proxy = false;
            this.fiscal_queue = [];
            return res;
        },
        init_sat: function (config) {
            var self = this;
            var j = {
                'sat_path': config.sat_path,
                'codigo_ativacao': config.cod_ativacao,
                'impressora': config.impressora,
                'printer_params': config.printer_params,
                'fiscal_printer_type': config.fiscal_printer_type,
                'assinatura': config.assinatura_sat,
            };
            self.message('init', {json: j}, {timeout: 5000})
        },
        keepalive: function () {
            var self = this;
            if (!this.keptalive) {
                this.keptalive = true;
                function status() {
                    self.connection.rpc('/hw_proxy/status_json', {}, {timeout: 2500})
                        .then(function (driver_status) {
                            if (!driver_status.hasOwnProperty("hw_fiscal")) {
                                self.pos.proxy.init_sat(self.pos.config);
                            } else {
                                self.set_connection_status('connected', driver_status);
                            }
                        }, function () {
                            if (self.get('status').driver_statusstatus !== 'connecting') {
                                self.set_connection_status('disconnected');
                            }
                        }).always(function () {
                        setTimeout(status, 5000);
                    });
                }
                status();
            }
        },
        send_order_sat: function (order) {
            var self = this;
            var json = order.export_for_printing();
            if (this.pos.debug) {
                console.log(json);
            }
            this.fiscal_queue.push(json);
            var aborted = false;
            return new Promise(function (resolve, reject) {
                if (self.fiscal_queue.length > 0) {
                    var j = self.fiscal_queue.shift();
                    self.message('enviar_cfe_sat', {json: j}, {timeout: 5000}).then(
                        (response) => {
                            console.log('Processing Request');
                            resolve( JSON.parse(response));
                        },
                        (error) => {
                            reject(error);
                        }
                    );
                }
            });

            // function send_sat_job() {
            //     if (self.fiscal_queue.length > 0) {
            //         var j = self.fiscal_queue.shift();
            //         // var r = self.fiscal_queue.shift();
            //         self.message('enviar_cfe_sat', {json: j}, {timeout: 5000})
            //             .then(function (result) {
            //                 var json_result = JSON.parse(result);
            //                 // TODO: Only one popup code!
            //                 if (typeof json_result === "string") {
            //                     self.pos.gui.show_popup('error-traceback', {
            //                         'title': _t('Erro SAT: '),
            //                         'body': _t(json_result)
            //                     });
            //                 } else {
            //
            //                     if (json_result['EEEEE'] === '06000') {
            //                         order.set_cfe_return(json_result);
            //                         // order.set_return_cfe(result['xml']);
            //                         // order.set_num_sessao_sat(result['numSessao']);
            //                         // order.set_chave_cfe(result['chave_cfe']);
            //
            //                         // self.pos.push_order(order);
            //                         // self.pos.pos_widget.posorderlist_screen.push_list_order_frontend(order);
            //                         // self.pos.get('order').destroy();
            //                     } else {
            //                         self.pos.gui.show_popup('error-traceback', {
            //                             'title': _t('Erro SAT: '),
            //                             'body': json_result,
            //                         });
            //                     }
            //                 }
            //             }, function (error) {
            //                 if (error) {
            //                     self.pos.gui.show_popup('error-traceback', {
            //                         'title': _t('Erro SAT: '),
            //                         'body': error.data.message,
            //                     });
            //                     return;
            //                 }
            //                 self.fiscal_queue.unshift(j)
            //                 // self.fiscal_queue.unshift(r)
            //             });
            //     }
            // }
            // send_sat_job();
        }
    //     remove_document_pontuations: function (document) {
    //         return document.replace(/[^\d]+/g, '');
    //     },
    //     cancel_last_order: function (order) {
    //         var self = this;
    //         order['cnpj_software_house'] = self.pos.config.cnpj_software_house;
    //         self.message('cancelar_cfe', {json: order}, {timeout: 5000})
    //             .then(function (result) {
    //                 if (result) {
    //                     var posOrderModel = new instance.web.Model('pos.order');
    //                     var posOrder = posOrderModel.call('refund', {
    //                         'ids': result.order_id,
    //                         'dados': result
    //                     })
    //                         .then(function (orders) {
    //                             self.gui.show_popup('error', {
    //                                 message: _t('Venda Cancelada!'),
    //                                 comment: _t('A venda foi cancelada com sucesso.'),
    //                             });
    //                             setTimeout(function () {
    //                                 self.pos.pos_widget.posorderlist_screen.get_last_orders();
    //                                 self.gui.back();
    //                             }, 4000);
    //                         }, function (error, event) {
    //                             event.preventDefault();
    //                             self.gui.show_popup('error', {
    //                                 'message': _t('Error: Tempo Excedido'),
    //                                 'comment': _t('Tempo limite de 30 minutos para cancelamento foi excedido.'),
    //                             });
    //                             return false;
    //                         });
    //                 } else {
    //                     self.gui.show_popup('error-traceback', {
    //                         'message': _t('Erro SAT: '),
    //                         'comment': _t(result['excessao']),
    //                     });
    //                 }
    //             }, function (error, event) {
    //                 event.preventDefault();
    //                 if (error) {
    //                     self.gui.show_popup('error-traceback', {
    //                         'message': _t('Erro SAT: '),
    //                         'comment': error.data.message,
    //                     });
    //                     return;
    //                 }
    //             });
    //     },
    //     reprint_cfe: function (order) {
    //         var self = this;
    //
    //         self.message('reprint_cfe', {json: order}, {timeout: 5000})
    //             .then(function (result) {
    //                 return;
    //             }, function (error) {
    //                 if (error) {
    //                     self.gui.show_popup('error-traceback', {
    //                         'message': _t('Erro SAT: '),
    //                         'comment': error.data.message,
    //                     });
    //                     return;
    //                 }
    //             });
    //     },
    });
});
