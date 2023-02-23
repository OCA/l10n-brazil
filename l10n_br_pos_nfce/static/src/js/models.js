/*
Copyright (C) 2022-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_nfce.models", function (require) {
    "use strict";

    const models = require("point_of_sale.models");
    const {Gui} = require("point_of_sale.Gui");

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            // CORE METHODS
            _super_order.initialize.apply(this, arguments, options);
            if (this.document_type === "65") {
                this.to_invoice = true;
            }
        },
        async document_send(component) {
            if (this.document_type !== "65") {
                return _super_order.document_send.apply(this, arguments);
            }
            if (!this.get_client()) {
                const anonimous_partner = this.pos.db.get_partner_by_id(
                    this.pos.config.partner_id[0]
                );
                this.set_client(anonimous_partner);
                component.trigger("close-popup");
            }

            return true;
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        push_and_invoice_order(order) {
            if (!this.document_type === "65") {
                return _super_posmodel.push_and_invoice_order.call(this);
            }
            var self = this;
            var invoiced = new Promise(function (resolveInvoiced, rejectInvoiced) {
                // eslint-disable-next-line
                if (!order.get_client()) {
                    rejectInvoiced({
                        code: 400,
                        message: "Missing Customer",
                        data: {},
                    });
                } else {
                    var order_id = self.db.add_order(order.export_as_JSON());

                    self.flush_mutex.exec(function () {
                        var done = new Promise(function (resolveDone, rejectDone) {
                            // Send the order to the server
                            // we have a 30 seconds timeout on this push.
                            // FIXME: if the server takes more than 30 seconds to accept the order,
                            // the client will believe it wasn't successfully sent, and very bad
                            // things will happen as a duplicate will be sent next time
                            // so we must make sure the server detects and ignores duplicated orders

                            var transfer = self._flush_orders(
                                [self.db.get_order(order_id)],
                                {timeout: 30000, to_invoice: true}
                            );

                            transfer.catch(function (error) {
                                rejectInvoiced(error);
                                rejectDone();
                            });

                            transfer.then(function (order_server_id) {
                                if (order_server_id.length) {
                                    resolveInvoiced(order_server_id);
                                    resolveDone();
                                } else {
                                    // The order has been pushed separately in batch when
                                    // the connection came back.
                                    // The user has to go to the backend to print the invoice
                                    rejectInvoiced({
                                        code: 401,
                                        message: "Backend Invoice",
                                        data: {order: order},
                                    });
                                    rejectDone();
                                }
                            });

                            return done;
                        });
                    });
                }
            });

            return invoiced;
        },

        _save_to_server: async function (orders, options) {
            const res = await _super_posmodel._save_to_server.call(
                this,
                orders,
                options
            );
            const invalid_orders = [];
            for (const option of res) {
                if (option.status_code !== "100") {
                    invalid_orders.push(option);
                }
            }
            if (invalid_orders.length === 1) {
                Gui.showPopup("ErrorPopup", {
                    title: "Erro ao emitir uma NFC-e",
                    body: `O pedido ${invalid_orders[0].pos_reference} teve o retorno ${invalid_orders[0].status_description}`,
                });
            } else if (invalid_orders.length > 1) {
                let msg = "Os seguintes pedidos: ";
                for (const option of invalid_orders) {
                    msg += ` ${option.pos_reference[1]},`;
                }
                msg += " tiveram sua NFC-e rejeitadas.";
                Gui.showPopup("ErrorPopup", {
                    title: "Erro ao emitir NFC-e",
                    body: msg,
                });
            }
            return res;
        },
    });
});
