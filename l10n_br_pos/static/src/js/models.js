/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/


odoo.define("l10n_br_pos.models", function (require) {

    var models = require("point_of_sale.models");
    var web_model = require("web.rpc");
    var PosModelParent = models.PosModel;
    var PosOrderParent = models.Order;
    var OrderLineParent = models.Orderline;
    var PosPaymentLineParent = models.Paymentline;

    models.PosModel = models.PosModel.extend({

        initialize: function (session, attributes) {

            this._super(this, session, attributes);

            PosModelParent.prototype.initialize.apply(this, arguments);
            arrange_elements(this);

            this.models.push({
                model: "res.country.state",
                fields: ["name", "country_id"],
                loaded: function (self, states) {
                    self.company.state = null;
                    self.states = states;
                }
            });

            this.models.push({
                model: "l10n_br_base.city",
                fields: ["name", "state_id"],
                loaded: function (self, cities) {
                    self.company.city = null;
                    self.cities = cities;
                }
            });

            this.models.push({
                model: "pos.config",
                fields: [],
                domain: function (self) {
                    return [["id", "=", self.pos_session.config_id[0]]];
                },
                loead: function (self, configs) {
                    self.config = configs[0];
                    self.config.use_proxy = self.config.iface_payment_terminal ||
                        self.config.iface_electronic_sale ||
                        self.config.iface_print_via_proxy ||
                        self.config.iface_scan_via_proxy ||
                        self.config.iface_cashdrawer ||
                        self.config.iface_sat_via_proxy;
                    self.barcode_reader.add_barcode_pattern({
                        "product": self.config.barcode_product,
                        "cashier": self.config.barcode_cashier,
                        "client": self.config.barcode_customer,
                        "weight": self.config.barcode_weight,
                        "discount": self.config.barcode_discount,
                        "price": self.config.barcode_price,
                    });

                    if (self.config.company_id[0] !== self.user.company_id[0]) {
                        throw new Error((
                            "Error: The Point of Sale User must belong to the same" +
                            " company as the Point of Sale. You are probably trying" +
                            " to load the point of sale as and administrator in a" +
                            " multi-company setup, with the administrator account" +
                            " set to the wrong company."
                        ));
                    }
                }
            });

            this.models.push({
                model: "res.partner",
                fields: ["name", "data_alteracao", "whatsapp", "gender", "birthdate",
                    "number", "street2", "opt_out", "create_date", "cnpj_cpf", "street",
                    "city", "state_id", "country_id", "phone", "zip", "mobile", "email",
                    "ean13", "write_date", "debit", "credit", "credit_limit",
                    "users_ids", "city_id",
                ],
                domain: [["customer", "=", true]],
                loaded: function (self, partners) {
                    self.partners = partners;
                    self.db.partner_by_id = [];
                    self.db.partner_sorted = [];
                    self.db.add_partner(partners);
                }
            });

            this.models.push({
                model: "res.company",
                fields: ["ambiente_sat", "cnpj_cpf", "inscr_est", "currency_id",
                    "email", "website", "company_registry", "name", "phone",
                    "partner_id", "country_id", "tax_calculation_rounding_method",
                ],
                ids: function (self) {
                    return [self.user.company_id[0]];
                },
                loaded: function (self, companies) {
                    self.company = companies[0];
                }
            });

        },

        find_model: function (model_name) {
            var lookup = {};
            for (var i = 0; i < this.models.length; i++) {
                if (this.models[i].model == model_name) {
                    lookup[i] = self.models[i];
                }
            }
            return lookup;
        },

        cancel_pos_order: function (chave_cfe) {
            var posOrderModel = models.Order;

            var posOrder = posOrderModel.call("cancel_last_order", {
                "chave_cfe": chave_cfe
            })
                .then(function (orders) {
                    console.log("cancel_pos_order");
                    console.log(this);
                    this.pos_widget.screen_selector.show_popup("error", {
                        message: ("Venda cancelada!"),
                        comment: ("A venda foi cancelada com sucesso."),
                    });
                });
        },

    });

    models.Order = models.Order.extend({
        initialize: function (attributes) {

            this._super(this, attributes);
            PosOrderParent.prototype.apply(this, arguments);
            this.attributes.cpf_nota = null;
            return this;

        },

        set_client: function (client) {
            PosOrderParent.prototype.set_client.apply(this, arguments);
            new web_model("res.partner").call(
                "get_credi_limit", [this.attributes.client["id"]]
            ).then(function (result) {
                self.attributes.client["credit_limit"] = result;
            })
        },

        verificar_pagamento_limite_credito: function () {
            var linhas_pagamento = this.attributes.paymentlines.models;
            for (var i = 0; i < linhas_pagamento.length; i++) {
                if (
                    linhas_pagamento[i].cashregister.journal.sat_payment_mode == "05" &&
                    !linhas_pagamento[i].cashregister.journal.pagamento_funconarios
                ) {
                    return true;
                }
            }
            return false;
        },

        funcionario_verificar_pagamento_limite_credito: function () {
            var linhas_pagamento = this.attributes.paymentLines.models;
            for (var i = 0; i < linhas_pagamento.length; i++) {
                if (
                    linhas_pagamento[i].cashregister.journal.sat_payment_mode == "05" &&
                    !linhas_pagamento[i].cashregister.journal.pagamento_funcionarios
                ) {
                    return true;
                }
            }
            return false;
        },

        add_payment_credito_loja: function (cashregister) {
            var paymentLines = this.get("paymentLines");
            var currentOrder = this.pos.get("selectedOrder");
            var total = this.getDueLeft();
            var newPaymentLine = new models.PaymentLine(
                {},
                {cashregister: cashregister, pos: this.pos}
            );
            if (cashregister.journal.pagamento_funcionarios) {
                newPaymentLine.set_amount(total);
            } else {
                if (this.attributes.client["credit_limit"] >= total) {
                    newPaymentLine.set_amount(total);
                } else {
                    newPaymentLine.set_amount(
                        this.attributes.client["credit_limit"]
                    );
                }
            }
            paymentLines.add(newPaymentLine);
            this.selectPaymentLine(newPaymentLine);
        },

        addPaymentLine: function (cashregister) {
            if (
                cashregister.journal.set_payment_mode == "05" && this.attributes.client
            ) {
                if (
                    cashregister.journal.pagamento_funcionarios &&
                    !this.funcionario_verificar_pagamento_limite_credito()
                ) {
                    pos_db = this.pos.db;
                    partner = pos_db.get_partner_by_id(
                        this.pos.partners,
                        this.attributes.client.cnpj_cpf,
                    );
                    if (partner.user_ids.length > 0 || (
                        this.attributes.client.user_ids &&
                        this.attributes.client.user_ids.length
                    )
                    ) {
                        this.add_payment_credito_loja(cashregister);
                    } else {
                        alert("Soment funcionários podem utilizar esta forma de" +
                            " pagamento");
                    }
                } else {
                    if (!this.verificar_pagamento_limite_credito()) {
                        if (this.attributes.client["credit_limit"] > 0) {
                            this.add_payment_credito_loja(cashregister);
                        } else {
                            alert("Este cliente não possui limite de crédito na loja!");
                        }
                    }
                }
            } else {
                if (
                    cashregister.journal.sat_payment_mode == "05" &&
                    !this.attributes.client
                ) {
                    if (cashregister.journal.pagamento_funcionarios) {
                        alert("Para usar este pagamento, é preciso selecionar um" +
                            " funcionário para a venda!");
                    } else {
                        alert("Para usar esse pagamento, é preciso selecionar um cliente" +
                            " para venda!");
                    }
                } else {
                    PosOrderParent.prototype.addPaymentLine.apply(this, arguments);
                }
            }
        },

        get_return_cfe: function () {
            return this.cfe_return;
        },

        set_return_cfe: function (xml) {
            this.cfe_return = xml;
        },

        get_chave_cfe: function () {
            return this.chave_cfe;
        },

        set_chave_cfe: function (chavecfe) {
            this.chave_cfe = chavecfe;
        },

        get_num_sessao_sat: function () {
            return this.num_sessao_sat;
        },

        set_num_sessao_sat: function (num_sessao_sat) {
            this.num_sessao_sat = num_sessao_sat;
        },

        export_for_printing: function () {
            var client = this.get("client");
            var company = this.pos.company;
            var status = this.pos.proxy.get("status");
            var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            var result = PosOrderParent.prototype.export_for_printing.call(this);
            if (sat_status == "connected") {
                var pos_config = this.pos.config;

                if (this.pos.company.ambiente_sat == "homologacao") {
                    company.cnpj = pos_config.cnpj_homologacao;
                    company.ie = pos_config.ie_homologacao;
                    company.cnpj_software_house = pos_config.cnpj_software_house;
                } else {
                    company.cnpj = this.pos.company.cnpj_cpf;
                    company.ie = this.pos.company.inscr_est;
                    company.cnpj_software_house = pos_config.cnpj_software_house;
                }

                result["company"] = {};
                result["configs_sat"] = {};
                result["pos_session_id"] = this.pos.pos_session.id;
                result["client"] = this.attributes.cpf_nota;
                result["company"]["cnpj"] = company.cnpj;
                result["company"]["ie"] = company.ie;
                result["company"]["cnpj_software_house"] = company.cnpj_software_house;
                result["configs_sat"]["sat_path"] = pos_config.sat_path;
                result["configs_sat"]["numero_caixa"] = pos_config.numero_caixa;
                result["configs_sat"]["cod_ativacao"] = pos_config.cod_ativacao;
                result["configs_sat"]["impressora"] = pos_config.impressora;
                result["configs_sat"]["printer_params"] = pos_config.printer_params;
                result["informacoes_adicionais"] = pos_config.company_id[1];

                return result;

            } else {

                result["pos_session_id"] = this.pos.pos_session.id;
                result["client"] = this.attributes.cpf_nota;
                result["cfe_return"] = this.get_return_cfe() ? this.get_return_cfe() : false;
                result["num_sessao_sat"] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
                result["chave_cfe"] = this.get_chave_cfe() ? this.get_chave_cfe() : false;
                result["informacoes_adicionais"] = "";

                return result;
            }
        },

        export_as_JSON: function () {
            var client = this.get("client");
            var company = this.pos.company;
            var status = this.pos.proxy.get("status");
            var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            var result = PosOrderParent.prototype.export_as_JSON.call(this);

            if (sat_status == "connected") {
                var pos_config = this.pos.config;

                if (this.pos.company.ambiente_sat == "homologacao") {
                    company.cnpj = pos_config.cnpj_homologacao;
                    company.ie = pos_config.ie_homologacao;
                    company.cnpj_software_house = pos_config.cnpj_software_house;
                } else {
                    company.cnpj = this.pos.company.cnpj_cpf;
                    company.ie = this.pos.company.inscr_est;
                    company.cnpj_software_house = pos_config.cnpj_software_house;
                }

                result["company"] = {};
                result["configs_sat"] = {};
                result["company"]["cnpj"] = company.cnpj;
                result["company"]["ie"] = company.ie;
                result["company"]["cnpj_software_house"] = company.cnpj_software_house;
                result["configs_sat"]["sat_path"] = pos_config.sat_path;
                result["configs_sat"]["numero_caixa"] = pos_config.numero_caixa;
                result["configs_sat"]["cod_ativacao"] = pos_config.cod_ativacao;
                result["configs_sat"]["impressora"] = pos_config.impressora;
                result["configs_sat"]["printer_params"] = pos_config.printer_params;
                result["client"] = this.attributes.cpf_nota;
                result["cfe_return"] = this.get_return_cfe() ? this.get_return_cfe() : false;
                result["num_sessao_sat"] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
                result["chave_cfe"] = this.get_chave_cfe() ? this.get_chave_cfe() : false;
                result["informacoes_adicionais"] = "";

                return result;
            } else {

                result["pos_session_id"] = this.pos.pos_session.id;
                result["client"] = this.attributes.cpf_nota;
                result["cfe_return"] = this.get_return_cfe() ? this.get_return_cfe() : false;
                result["num_sessao_sat"] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
                result["chave_cfe"] = this.get_chave_cfe() ? this.get_chave_cfe() : false;
                result["informacoes_adicionais"] = "";

                return result;
            }
        },
    });

    models.Orderline = models.Orderline.extend({

        export_for_printing: function () {
            var result = OrderLineParent.prototype.export_as_JSON.call(this);
            var produto = this.get_product();

            result["quantity"] = this.get_quantity();
            result["unit_name"] = this.get_unit().name;
            result["price"] = this.get_unit_price();
            result["discount"] = this.get_discount();
            result["product_name"] = produto.name;
            result["price_display"] = this.get_display_price();
            result["price_with_tax"] = this.get_price_with_tax();
            result["price_without_tax"] = this.get_price_without_tax();
            result["tax"] = this.get_tax();
            result["product_description"] = produto.description;
            result["product_description_sale"] = produto.description_sale;
            result["product_default_code"] = produto.default_code;
            result["fiscal_classification_id"] = produto.fiscal_classification_id;
            result["estimated_taxes"] = produto.estd_national_taxes_perct / 100;
            result["origin"] = produto.origin;

            return result;
        }

    });

    models.Paymentline = models.Paymentline.extend({
        set_payment_term: function (payment_term) {
            this.payment_term = payment_term;
        },

        get_payment_term: function () {
            return this.payment_term;
        },

        export_as_JSON: function () {
            var result = PosPaymentLineParent.prototype.export_as_JSON.call(this);
            result["sat_payment_mode"] = this.cashregister.journal.sat_payment_mode;
            result["sat_card_accrediting"] = this.cashregister.journal.sat_card_accrediting;
            return result;
        },

        export_for_printing: function () {
            var result = PosPaymentLineParent.prototype.export_for_printing.call(this);
            result["sat_payment_mode"] = this.cashregister.journal.sat_payment_mode;
            result["sat_card_accrediting"] = this.cashregister.journal.sat_card_accrediting;
            return result;
        }

    });

    function arrange_elements(pos_model) {

        var product_product_model = pos_model.find_model("product.product");

        if (_.size(product_product_model) == 1) {
            var res_partner_index = parseInt(Object.keys(product_product_model)[0]);
            pos_model.models[res_partner_index].fields.push(
                "fiscal_classification_id",
                "origin",
                "estd_national_taxes_perct",
                "name",
            );

            pos_model.models[res_partner_index].domain.push([
                "qty_available", ">", "0"
            ]);
        }

        var account_journal_model = pos_model.find_model("account.journal");

        if (_.size(account_journal_model) == 1) {
            var account_journal_model = parseInt(Object.keys(account_journal_model)[0]);
            pos_model.models[res_partner_index].fields.push(
                "sat_payment_mode",
                "sat_card_accrediting",
            );
        }

        var res_partner_model = pos_model.find_model("res.partner");

        if (_.size(res_partner_model) == 1) {
            var res_partner_index = parseInt(Object.keys(res_partner_model)[0]);
            pos_model.models[res_partner_index].fields.push(
                "legal_name",
                "cnpj_cpf",
                "create_date",
                "inscr_est",
                "inscr_mun",
                "suframa",
                "district",
                "number",
                "country_id",
                "state_id",
                "city_id",
            )
        }

        var res_company_model = pos_model.find_model("res.company");

        if (_.size(res_company_model) == 1) {
            var res_company_index = parseInt(Object.keys(res_company_model)[0]);
            pos_model.models[res_company_index].fids.push(
                "legal_name",
                "cnpj_cpf",
                "inscr_est",
                "inscr_mun",
                "suframa",
                "district",
                "number",
                "country_id",
                "state_id",
                "city_id",
            )
        }

    }

});