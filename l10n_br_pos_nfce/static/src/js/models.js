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

        export_for_printing: function (json) {
            json = _super_order.export_for_printing.call(this, json);

            if (this.pos.config.simplified_document_type !== "65") return json;

            const company = this.pos.company;
            const {
                cnpj_cpf,
                inscr_est,
                legal_name,
                street_name,
                street_number,
                district,
                city_id,
                zip,
                state_id,
            } = company;
            const {nfce_environment} = this.pos.config;

            const companyInfo = {
                cnpj_cpf,
                inscr_est,
                legal_name,
                address: {
                    street_name,
                    street_number,
                    district,
                    city: city_id[1],
                    zip,
                    state: state_id[1],
                },
            };

            json.company = Object.assign({}, this.company, companyInfo);
            json.nfce_environment = nfce_environment;

            const additionalInfo = this._buildNFCeAdditionalInfo();

            return {...json, ...additionalInfo};
        },

        _buildNFCeAdditionalInfo: function () {
            return {
                url_consulta: this.url_consulta,
                qr_code: this.qr_code,
                authorization_date_string: this.authorization_date_string,
                document_date_string: this.document_date_string,
            };
        },

        _prepare_fiscal_json: function (json) {
            _super_order._prepare_fiscal_json.apply(this, arguments);
            json.document_type = this.document_type;
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
            const response = await _super_posmodel._save_to_server.call(
                this,
                orders,
                options
            );

            if (this.env.pos.config.simplified_document_type !== "65") return response;

            for (const orderOption of response) {
                const order = this.get_order();
                Object.assign(order, {
                    authorization_protocol: orderOption.authorization_protocol,
                    document_key: orderOption.document_key,
                    document_number: orderOption.document_number,
                    url_consulta: orderOption.url_consulta,
                    qr_code: orderOption.qr_code,
                    authorization_date_string: orderOption.authorization_date_string,
                    document_date_string: orderOption.document_date_string,
                    document_serie: orderOption.document_serie,
                });
            }

            const invalidOrders = response.filter(
                ({status_code}) => status_code !== "100"
            );
            const validOrders = response.filter(
                ({status_code}) => status_code === "100"
            );

            if (validOrders.length > 0) {
                Gui.showPopup("ConfirmPopup", {
                    title: "NFC-e Issuance",
                    body: "NFC-e issued successfully.",
                });
            }

            if (invalidOrders.length > 1) {
                const invalidOrdersRefs = invalidOrders.map(({pos_reference}) =>
                    pos_reference[1].join(", ")
                );
                const invalidOrdersObj = invalidOrders.reduce((obj, order) => {
                    obj[order.pos_reference] = order.status_description;
                    return obj;
                }, {});
                Gui.showPopup("ErrorPopup", {
                    title: "Error Issuing NFC-e",
                    body: `The following orders had their NFC-e rejected: ${invalidOrdersRefs}.`,
                });
                console.error(
                    "l10n_br_pos_nfce ~ file: models.js:185 ~ invalidOrdersObj:",
                    invalidOrdersObj
                );
            }

            return response;
        },
    });
});
