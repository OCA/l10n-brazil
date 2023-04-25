/*
Copyright (C) 2022-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_nfce.models", function (require) {
    "use strict";

    const models = require("point_of_sale.models");
    const {ChaveEdoc} = require("l10n_br_pos_nfce.utils");

    const BRAZILIAN_STATES_IBGE_CODE_MAP = {
        "Acre (BR)": "12",
        "Alagoas (BR)": "27",
        "Amazonas (BR)": "13",
        "Amapá (BR)": "16",
        "Bahia (BR)": "29",
        "Ceará (BR)": "23",
        "Distrito Federal (BR)": "53",
        "Espírito Santo (BR)": "32",
        "Goiás (BR)": "52",
        "Maranhão (BR)": "21",
        "Minas Gerais (BR)": "31",
        "Mato Grosso do Sul (BR)": "50",
        "Mato Grosso (BR)": "51",
        "Pará (BR)": "15",
        "Paraíba (BR)": "25",
        "Pernambuco (BR)": "26",
        "Piauí (BR)": "22",
        "Paraná (BR)": "41",
        "Rio de Janeiro (BR)": "33",
        "Rio Grande do Norte (BR)": "24",
        "Rondônia (BR)": "11",
        "Roraima (BR)": "14",
        "Rio Grande do Sul (BR)": "43",
        "Santa Catarina (BR)": "42",
        "Sergipe (BR)": "28",
        "São Paulo (BR)": "35",
        "Tocantins (BR)": "17",
    };

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

        _save_to_server: async function (orders, options = {}) {
            if (this.env.pos.config.simplified_document_type !== "65") {
                return _super_posmodel._save_to_server.call(this, orders, options);
            }

            if (!orders || !orders.length) {
                return Promise.resolve([]);
            }

            const self = this;
            const timeout =
                typeof options.timeout === "number"
                    ? options.timeout
                    : 30000 * orders.length;

            const order_ids_to_sync = _.pluck(orders, "id");

            const args = [
                _.map(orders, (order) => {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                }),
            ];

            return this.rpc(
                {
                    model: "pos.order",
                    method: "create_from_ui",
                    args: args,
                    kwargs: {context: this.session.user_context},
                },
                {
                    timeout: timeout,
                    shadow: !options.to_invoice,
                }
            )
                .then(async (server_ids) => {
                    _.each(order_ids_to_sync, (order_id) => {
                        self.db.remove_order(order_id);
                    });
                    self.set("failed", false);
                    await self._fillNFCeAdditionalInfo(server_ids);
                    await self._updateNFCeSerieNumber();
                    return server_ids;
                })
                .catch((reason) => {
                    const error = reason.message;
                    console.error("Failed to send orders:", orders);
                    if (error.code === 200) {
                        if (
                            (!self.get("failed") || options.show_error) &&
                            !options.to_invoice
                        ) {
                            self.set("failed", error);
                            throw error;
                        }
                    }
                    self._contingenciaNFCe(orders);
                    self.set("failed", true);
                    return orders.map((order) => {
                        return {
                            pos_reference: order.data.name,
                        };
                    });
                });
        },

        _fillNFCeAdditionalInfo: function (orders) {
            for (const orderOption of orders) {
                const order = this.get_order();
                Object.assign(order, {
                    authorization_protocol: orderOption.authorization_protocol,
                    document_key: orderOption.document_key,
                    document_number: orderOption.document_number,
                    url_consulta: orderOption.url_consulta,
                    qr_code: orderOption.qr_code,
                    authorization_date_string: orderOption.authorization_date,
                    document_date_string: orderOption.document_date,
                    document_serie: orderOption.document_serie,
                });
            }

            const invalidOrders = orders.filter(
                ({status_code}) => status_code !== "100"
            );
            const validOrders = orders.filter(({status_code}) => status_code === "100");

            if (validOrders.length > 0) {
                console.log("NFC-e issued successfully");
            }

            if (invalidOrders.length > 1) {
                const invalidOrdersRefs = invalidOrders.map(({pos_reference}) =>
                    pos_reference[1].join(", ")
                );
                console.warn(`NFC-e not issued: ${invalidOrdersRefs.join(", ")}`);
            }
        },

        _contingenciaNFCe: function (orders) {
            const state = this.env.pos.company.state_id[1];
            const cnpj = this.env.pos.company.cnpj_cpf.replace(/([^\w ]|_)/g, "");
            const currentDate = new Date();
            const ordersToSend = this.env.pos.db.get_orders();
            // Get the two last digits of year and month with padstart 2
            const yearMonth =
                currentDate.getFullYear().toString().substr(-2) +
                (currentDate.getMonth() + 1).toString().padStart(2, "0");
            for (let i = 0; i < orders.length; i++) {
                const currentOrder = this.get_order();
                if (!currentOrder.document_number) {
                    currentOrder.document_serie = this.env.pos.config.nfce_document_serie_code.padStart(
                        3,
                        "0"
                    );
                    currentOrder.document_number = this.env.pos.config.nfce_document_serie_sequence_number_next;
                    const chaveEdoc = new ChaveEdoc(
                        false,
                        BRAZILIAN_STATES_IBGE_CODE_MAP[state],
                        yearMonth,
                        cnpj,
                        this.env.pos.config.simplified_document_type,
                        currentOrder.document_serie,
                        currentOrder.document_number.toString().padStart(9, "0"),
                        "9"
                    );
                    currentOrder.document_key = chaveEdoc.generatedChave;
                    currentOrder.document_date_string = currentDate.toLocaleString();
                    this.env.pos.config.nfce_document_serie_sequence_number_next += 1;
                    for (let j = 0; j < ordersToSend.length; j++) {
                        if (orders[i].id === ordersToSend[j].id) {
                            ordersToSend[j].data.document_key =
                                currentOrder.document_key;
                            ordersToSend[j].data.document_number =
                                currentOrder.document_number;
                            break;
                        }
                    }
                }
            }
        },

        _updateNFCeSerieNumber: function () {
            const self = this;
            this.rpc({
                model: "pos.config",
                method: "update_nfce_serie_number",
                args: [
                    [],
                    this.env.pos.config.id,
                    this.env.pos.config.nfce_document_serie_sequence_number_next,
                ],
            }).then((result) => {
                console.log("NFC-e serie number updated successfully");
                self.env.pos.config.nfce_document_serie_sequence_number_next = result;
            });
        },
    });
});
