/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.devices", function (require) {
    "use strict";
    var devices = require("point_of_sale.devices");
    var FiscalDocumentCFe = require("l10n_br_pos_cfe.FiscalDocumentCFe")
        .FiscalDocumentCFe;

    var ProxyDeviceSuper = devices.ProxyDevice;

    devices.ProxyDevice = devices.ProxyDevice.extend({
        init: function () {
            var res = ProxyDeviceSuper.prototype.init.apply(this, arguments);
            var self = this;

            this.on("change:status", this, function (eh, status) {
                status = status.newValue;
                if (status.status === "connected" && self.fiscal_device) {
                    self.fiscal_device.send_order();
                    // TODO: Criar uma abstração na fila para processar todas as ações.
                }
            });

            return res;
        },
        set_connection_status: function (status, drivers, msg = "") {
            ProxyDeviceSuper.prototype.set_connection_status.apply(this, arguments);
            if (status === "connected" && this.fiscal_device) {
                var oldstatus = this.get("status");
                if (oldstatus.drivers) {
                    if (!oldstatus.drivers.hw_fiscal) {
                        this.fiscal_device.init_job();
                    }
                }
            }
        },
        connect: function (url) {
            var result = ProxyDeviceSuper.prototype.connect.apply(this, arguments);
            this.connect_to_fiscal_device();
            return result;
        },
        autoconnect: function (options) {
            var result = ProxyDeviceSuper.prototype.autoconnect.apply(this, arguments);
            this.connect_to_fiscal_device();
            return result;
        },
        keepalive: function (options) {
            var result = ProxyDeviceSuper.prototype.keepalive.apply(this, arguments);
            return result;
        },
        connect_to_fiscal_device: function () {
            if (this.pos.config.iface_fiscal_via_proxy) {
                this.fiscal_device = new FiscalDocumentCFe(this.host, this.pos);
                this.fiscal_device_contingency = this.fiscal_device;
            }
        },
        reprint_cfe: function (order) {
            var self = this;
            $(".selection").append(
                "<div data-item-index='3' class='selection-item '>Imprimindo Cupom Fiscal</div>"
            );
            self.message("reprint_cfe", {json: order}, {timeout: 5000}).then(
                function () {
                    return;
                },
                function (error) {
                    if (error) {
                        self.gui.show_popup("error-traceback", {
                            title: _t("Erro SAT: "),
                            body: error.data.message,
                        });
                        return;
                    }
                }
            );
        },
        send_order_sat: function (order) {
            var self = this;
            var json = order.export_for_printing();
            if (this.pos.debug) {
                console.log(json);
            }
            this.fiscal_queue.push(json);
            return new Promise(function (resolve, reject) {
                if (self.fiscal_queue.length > 0) {
                    var j = self.fiscal_queue.shift();
                    $(".selection").append(
                        "<div data-item-index='2' class='selection-item '>Transmitir CF-e para o SAT</div>"
                    );
                    self.pos.proxy
                        .message(
                            "sessao_sat",
                            {json: self.pos.config.sessao_sat},
                            {timeout: 5000}
                        )
                        .then(
                            function (result) {
                                if (result.num_sessao != self.pos.config.sessao_sat) {
                                    self.message(
                                        "enviar_cfe_sat",
                                        {json: j},
                                        {timeout: 5000}
                                    ).then(
                                        (response) => {
                                            console.log("Processing Request");
                                            try {
                                                var response_as_json = JSON.parse(
                                                    response
                                                );
                                            } catch (error) {
                                                self.pos.gui.show_popup(
                                                    "error-traceback",
                                                    {
                                                        title: _t("Erro SAT: "),
                                                        body: _t(response),
                                                    }
                                                );
                                                return;
                                            }
                                            self.reprint_cfe({
                                                xml_cfe_venda:
                                                    response_as_json.arquivoCFeSAT,
                                            });
                                            var config_id = self.pos.config.id;
                                            self.pos.config.sessao_sat++;
                                            rpc.query({
                                                model: "pos.config",
                                                method: "update_sessao_sat",
                                                args: [config_id],
                                            });
                                            resolve(response_as_json);
                                        },
                                        (error) => {
                                            reject(error);
                                        }
                                    );
                                } else {
                                    self.pos.gui.show_popup("error-traceback", {
                                        title: _t("Erro SAT: "),
                                        body: "Este cupom já foi transmitido!",
                                    });
                                    return;
                                }
                            },
                            function (error) {
                                if (error) {
                                    self.pos.gui.show_popup("error-traceback", {
                                        title: _t("Erro SAT: "),
                                        body: error.data.message,
                                    });
                                    return;
                                }
                            }
                        );
                }
            });

            // Function send_sat_job() {
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
        },
        cancel_order: function (order) {
            var self = this;
            order.cnpj_software_house = self.pos.config.cnpj_software_house;
            self.pos.proxy
                .message(
                    "sessao_sat",
                    {json: self.pos.config.sessao_sat},
                    {timeout: 5000}
                )
                .then(
                    function (result) {
                        if (result.num_sessao != self.pos.config.sessao_sat) {
                            self.message(
                                "cancelar_cfe",
                                {json: order},
                                {timeout: 5000}
                            ).then(
                                function (result) {
                                    if (result && typeof result === "object") {
                                        self.reprint_cfe({
                                            xml_cfe_venda: order.xml_cfe_venda,
                                            xml_cfe_cacelada: result.xml,
                                            canceled_order: true,
                                        });
                                        rpc.query({
                                            model: "pos.order",
                                            method: "cancelar_order",
                                            args: [result],
                                        }).then(
                                            function () {
                                                self.pos.gui.show_popup("alert", {
                                                    tittle: _t("Venda Cancelada!"),
                                                    body: _t(
                                                        "A venda foi cancelada com sucesso."
                                                    ),
                                                });
                                                var config_id = self.pos.config.id;
                                                self.pos.config.sessao_sat++;
                                                rpc.query({
                                                    model: "pos.config",
                                                    method: "update_sessao_sat",
                                                    args: [config_id],
                                                });
                                            },
                                            function (error, event) {
                                                event.preventDefault();
                                                self.pos.gui.show_popup("error", {
                                                    title: _t("Error: Tempo Excedido"),
                                                    body: _t(
                                                        "Tempo limite de 30 minutos para cancelamento foi excedido."
                                                    ),
                                                });
                                                return false;
                                            }
                                        );
                                    } else {
                                        self.pos.gui.show_popup("error", {
                                            tittle: _t("Erro SAT: "),
                                            body: _t(result),
                                        });
                                    }
                                },
                                function (error, event) {
                                    event.preventDefault();
                                    if (error) {
                                        self.pos.gui.show_popup("error-traceback", {
                                            title: _t("Erro SAT: "),
                                            body: error.data.message,
                                        });
                                        return;
                                    }
                                }
                            );
                        } else {
                            self.pos.gui.show_popup("error-traceback", {
                                title: _t("Erro SAT: "),
                                body: "Este cupom já foi transmitido!",
                            });
                            return;
                        }
                    },
                    function (error) {
                        if (error) {
                            self.gui.show_popup("error-traceback", {
                                title: _t("Erro SAT: "),
                                body: error.data.message,
                            });
                            return;
                        }
                    }
                );
        },
        //     Remove_document_pontuations: function (document) {
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
    });
});
