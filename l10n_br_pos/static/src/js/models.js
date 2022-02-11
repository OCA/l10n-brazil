/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos.models", function (require) {
    var models = require("point_of_sale.models");
    var util = require("l10n_br_pos.util");
    var partner_company_fields = [
        "legal_name",
        "cnpj_cpf",
        "inscr_est",
        "ind_ie_dest",
        "inscr_mun",
        "suframa",
        "tax_framework",
        "street_number",
        "city_id",
    ];
    models.load_fields("res.partner", partner_company_fields);
    models.load_fields(
        "res.company",
        partner_company_fields.concat([
            "ambiente_sat",
            "cnpj_software_house",
            "sign_software_house",
            "tax_framework",
        ])
    );
    models.load_fields("uom.uom", ["code"]);
    models.load_fields("product.product", [
        "tax_icms_or_issqn",
        "fiscal_type",
        "icms_origin",
        "fiscal_genre_code",
        "ncm_id",
        "ncm_code",
        "ncm_code_exception",
        "nbm_id",
        "fiscal_genre_id",
        "service_type_id",
        "city_taxation_code_id",
        "ipi_guideline_class_id",
        "ipi_control_seal_id",
        "nbs_id",
        "cest_id",
    ]);
    models.load_fields("account.journal", ["sat_payment_mode", "sat_card_accrediting"]);

    models.load_models({
        model: "l10n_br_pos.product_fiscal_map",
        fields: [
            // TODO: Load only required fields
            // 'product_tmpl_id',
            // 'icms_cst_code',
            // 'icms_percent',
            // 'icms_effective_percent',
            // 'pis_cst_code',
            // 'pis_base',
            // 'pis_percent',
            // 'cofins_cst_code',
            // 'cofins_base',
            // 'cofins_percent',
            // 'cfop',
            // 'additional_data',
            // 'amount_estimate_tax',
        ],
        domain: function (self) {
            return [["pos_config_id", "=", self.config.id]];
        },
        loaded: function (self, lines) {
            self.fiscal_map = lines;
            self.fiscal_map_by_template_id = {};
            lines.forEach(function (line) {
                self.fiscal_map_by_template_id[line.product_tmpl_id[0]] = line;
            });
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments, options);

            this.cnpj_cpf = this.cnpj_cpf || null;
            this.document_authorization_date = this.document_authorization_date || null;
            this.document_status_code = this.document_status_code || null;
            this.document_status_name = this.document_status_name || null;
            this.document_session_number = this.document_session_number || null;
            this.document_key = this.document_key || null;
            this.document_file = this.document_file || null;

            if (options.json) {
                this.init_from_JSON(options.json);
            } else {
                this.fiscal_operation_id = this.pos.config.out_pos_fiscal_operation_id[0];
                this.document_type_id = this.pos.config.simplified_document_type_id[0];
                this.document_type = this.pos.config.simplified_document_type;
            }

            this.save_to_db();
        },
        set_cfe_return: function (json_result) {
            console.log("set_cfe_return");
            $(".selection").append(
                "<div data-item-index='4' class='selection-item '>Salvando Cupom Fiscal no Back Office</div>"
            );
            this.document_authorization_date = json_result.timeStamp;
            this.document_status_code = json_result.EEEEE;
            this.document_status_name = json_result.mensagem;
            this.document_session_number = json_result.numeroSessao;
            this.document_key = json_result.chaveConsulta;
            this.document_file = json_result.arquivoCFeSAT;
            // TODO: Verificar se outros campos devem ser setados;
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
        set_cnpj_cpf: function (cnpj_cpf) {
            if (util.validate_cnpj_cpf(cnpj_cpf)){
                this.assert_editable();
                this.cnpj_cpf = cnpj_cpf;
                this.trigger("change", this);
                return true;
            } else {
                this.pos.gui.show_popup("alert", {
                    title: _t('Invalid CNPJ / CPF !'),
                    body: _t('Enter a valid CNPJ / CPF number'),
                });
                return false;
            }

        },
        get_cnpj_cpf: function () {
            return this.cnpj_cpf;
        },
        clone: function () {
            var order = _super_order.clone.call(this);
            order.cnpj_cpf = null;
            return order;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.call(this);
            json.cnpj_cpf = this.cnpj_cpf;
            json.fiscal_operation_id = this.fiscal_operation_id;
            json.document_type = this.document_type;
            json.document_type_id = this.document_type_id;
            json.document_authorization_date = this.document_authorization_date;
            json.document_status_code = this.document_status_code;
            json.document_status_name = this.document_status_name;
            json.document_session_number = this.document_session_number;
            json.document_key = this.document_key;
            json.document_file = this.document_file;
            return json;
        },
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.cnpj_cpf = json.cnpj_cpf;
            this.fiscal_operation_id = json.fiscal_operation_id;
            this.document_type = json.document_type;
            this.document_type_id = json.document_type_id;
        },
        export_for_printing: function () {
            var result = _super_order.export_for_printing.apply(this, arguments);
            // Result.table = this.table ? this.table.name : undefined;
            // result.floor = this.table ? this.table.floor.name : undefined;
            // result.customer_count = this.get_customer_count();
            result.orderlines = _.filter(result.orderlines, function (line) {return line.price !== 0; });
            var company = this.pos.company;
            var pos_config = this.pos.config;

            if (this.pos.company.ambiente_sat == "producao") {
                company.cnpj = this.pos.company.cnpj_cpf;
                company.ie = this.pos.company.inscr_est;
                company.cnpj_software_house = pos_config.cnpj_software_house;
            } else {
                company.cnpj = pos_config.cnpj_homologacao;
                company.ie = pos_config.ie_homologacao;
                company.cnpj_software_house = pos_config.cnpj_software_house;
            }

            result.company = {};
            result.configs_sat = {};
            result.pos_session_id = this.pos.pos_session.id;
            result.client = this.get_cnpj_cpf();
            result.company.cnpj = company.cnpj;
            result.company.ie = company.ie;
            result.company.cnpj_software_house = company.cnpj_software_house;
            result.company.tax_framework = company.tax_framework;
            result.configs_sat.sat_path = pos_config.sat_path;
            result.configs_sat.numero_caixa = pos_config.numero_caixa;
            result.configs_sat.cod_ativacao = pos_config.cod_ativacao;
            result.configs_sat.impressora = pos_config.impressora;
            result.configs_sat.printer_params = pos_config.printer_params;
            result.additional_data = pos_config.additional_data;

            return result;
        },
        // Export_for_printing: function () {
        //     var client = this.get("client");
        //     var status = this.pos.proxy.get("status");
        //     var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
        //     var result = PosOrderParent.prototype.export_for_printing.call(this);
        //     if (sat_status == "connected") {
        //              CODIGO MIGRADO ACIMA!!!!
        //     } else {
        //         result["pos_session_id"] = this.pos.pos_session.id;
        //         result["client"] = this.attributes.cpf_nota;
        //         result["cfe_return"] = this.get_return_cfe() ? this.get_return_cfe() : false;
        //         result["num_sessao_sat"] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
        //         result["chave_cfe"] = this.get_chave_cfe() ? this.get_chave_cfe() : false;
        //         result["informacoes_adicionais"] = "";
        //         return result;
        //     }
        // },
        // export_as_JSON: function () {
        //     var client = this.get("client");
        //     var company = this.pos.company;
        //     var status = this.pos.proxy.get("status");
        //     var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
        //     var result = PosOrderParent.prototype.export_as_JSON.call(this);
        //     if (sat_status == "connected") {
        //         var pos_config = this.pos.config;
        //         if (this.pos.company.ambiente_sat == "homologacao") {
        //             company.cnpj = pos_config.cnpj_homologacao;
        //             company.ie = pos_config.ie_homologacao;
        //             company.cnpj_software_house = pos_config.cnpj_software_house;
        //         } else {
        //             company.cnpj = this.pos.company.cnpj_cpf;
        //             company.ie = this.pos.company.inscr_est;
        //             company.cnpj_software_house = pos_config.cnpj_software_house;
        //         }
        //         result["company"] = {};
        //         result["configs_sat"] = {};
        //         result["company"]["cnpj"] = company.cnpj;
        //         result["company"]["ie"] = company.ie;
        //         result["company"]["cnpj_software_house"] = company.cnpj_software_house;
        //         result["configs_sat"]["sat_path"] = pos_config.sat_path;
        //         result["configs_sat"]["numero_caixa"] = pos_config.numero_caixa;
        //         result["configs_sat"]["cod_ativacao"] = pos_config.cod_ativacao;
        //         result["configs_sat"]["impressora"] = pos_config.impressora;
        //         result["configs_sat"]["printer_params"] = pos_config.printer_params;
        //         result["client"] = this.attributes.cpf_nota;
        //         result["cfe_return"] = this.get_return_cfe() ? this.get_return_cfe() : false;
        //         result["num_sessao_sat"] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
        //         result["chave_cfe"] = this.get_chave_cfe() ? this.get_chave_cfe() : false;
        //         result["informacoes_adicionais"] = "";
        //         return result;
        //     } else {
        //         result["pos_session_id"] = this.pos.pos_session.id;
        //         result["client"] = this.attributes.cpf_nota;
        //         result["cfe_return"] = this.get_return_cfe() ? this.get_return_cfe() : false;
        //         result["num_sessao_sat"] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
        //         result["chave_cfe"] = this.get_chave_cfe() ? this.get_chave_cfe() : false;
        //         result["informacoes_adicionais"] = "";
        //         return result;
        //     }
        // },
    });

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function () {
            var result = _super_order_line.export_for_printing.apply(this, arguments);
            var self = this;
            product = this.get_product();
            var product_fiscal_map =
                self.pos.fiscal_map_by_template_id[product.product_tmpl_id];
            // Result["price"] = this.get_unit_price();
            // result["product_name"] = produto.name;
            // result["estimated_taxes"] = produto.estd_national_taxes_perct / 100;
            // result["origin"] = produto.origin;
            result.additional_data = product_fiscal_map.additional_data || '';
            result.amount_estimate_tax = product_fiscal_map.amount_estimate_tax;
            result.cest_id = product.cest_id;
            result.cfop = product_fiscal_map.cfop_code;
            result.city_taxation_code_id = product.city_taxation_code_id;
            result.cofins_base = product_fiscal_map.cofins_base;
            result.cofins_cst_code = product_fiscal_map.cofins_cst_code;
            result.cofins_percent = product_fiscal_map.cofins_percent;
            result.company_tax_framework = product_fiscal_map.company_tax_framework;
            result.fiscal_genre_code = product.fiscal_genre_code;
            result.fiscal_genre_id = product.fiscal_genre_id;
            result.fiscal_type = product.fiscal_type;
            result.icms_cst_code = product_fiscal_map.icms_cst_code;
            result.icms_effective_percent = product_fiscal_map.icms_effective_percent;
            result.icms_origin = product.icms_origin;
            result.icms_percent = product_fiscal_map.icms_percent;
            result.icmssn_percent = product_fiscal_map.icmssn_percent;
            result.ipi_control_seal_id = product.ipi_control_seal_id;
            result.ipi_guideline_class_id = product.ipi_guideline_class_id;
            result.nbs_id = product.nbs_id;
            result.ncm = product_fiscal_map.ncm_code === "00000000" ? "99999999" : product_fiscal_map.ncm_code;
            result.ncm_code_exception = product_fiscal_map.ncm_code_exception;
            result.pis_base = product_fiscal_map.pis_base;
            result.pis_cst_code = product_fiscal_map.pis_cst_code;
            result.pis_percent = product_fiscal_map.pis_percent;
            result.product_default_code = product.default_code;
            result.product_ean = product.barcode;
            result.service_type_id = product.service_type_id;
            result.tax_icms_or_issqn = product.tax_icms_or_issqn;
            result.unit_code = this.get_unit().code;
            return result;
        },
    });

    var _super_payment_line = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        export_for_printing: function () {
            var result = _super_payment_line.export_for_printing.apply(this, arguments);
            result.sat_payment_mode = this.cashregister.journal.sat_payment_mode;
            result.sat_card_accrediting = this.cashregister.journal.sat_card_accrediting;
            return result;
        },
        export_as_JSON: function () {
            var result = _super_payment_line.export_as_JSON.apply(this, arguments);
            result.sat_payment_mode = this.cashregister.journal.sat_payment_mode;
            result.sat_card_accrediting = this.cashregister.journal.sat_card_accrediting;
            return result;
        },
    });

    var _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        // Initialize: function(session, attributes) {
        //     this.cnpj_cpf = null;
        //     return _super_posmodel.initialize.call(this,session,attributes);
        // },
        get_cnpj_cpf: function () {
            var order = this.get_order();
            if (order) {
                return order.get_cnpj_cpf();
            }
            return null;
        },
    });

    var _config = _.findWhere(models.PosModel.prototype.models, {model: "pos.config"});
    var old_loaded = _config.loaded;
    _config.loaded = function (self, configs) {
        old_loaded(self, configs);
        if (self.config.iface_fiscal_via_proxy) {
            self.config.use_proxy = true;
        }
    };

    //     Initialize: function (session, attributes) {
    //         this._super(this, session, attributes);
    //         PosModelParent.prototype.initialize.apply(this, arguments);
    //         arrange_elements(this);
    //         this.models.push({
    //             model: "res.country.state",
    //             fields: ["name", "country_id"],
    //             loaded: function (self, states) {
    //                 self.company.state = null;
    //                 self.states = states;
    //             }
    //         });
    //         this.models.push({
    //             model: "l10n_br_base.city",
    //             fields: ["name", "state_id"],
    //             loaded: function (self, cities) {
    //                 self.company.city = null;
    //                 self.cities = cities;
    //             }
    //         });
    //         this.models.push({
    //             model: "pos.config",
    //             fields: [],
    //             domain: function (self) {
    //                 return [["id", "=", self.pos_session.config_id[0]]];
    //             },
    //             loead: function (self, configs) {
    //                 self.config = configs[0];
    //                 self.config.use_proxy = self.config.iface_payment_terminal ||
    //                     self.config.iface_electronic_sale ||
    //                     self.config.iface_print_via_proxy ||
    //                     self.config.iface_scan_via_proxy ||
    //                     self.config.iface_cashdrawer ||
    //                     self.config.iface_sat_via_proxy;
    //                 self.barcode_reader.add_barcode_pattern({
    //                     "product": self.config.barcode_product,
    //                     "cashier": self.config.barcode_cashier,
    //                     "client": self.config.barcode_customer,
    //                     "weight": self.config.barcode_weight,
    //                     "discount": self.config.barcode_discount,
    //                     "price": self.config.barcode_price,
    //                 });
    //                 if (self.config.company_id[0] !== self.user.company_id[0]) {
    //                     throw new Error((
    //                         "Error: The Point of Sale User must belong to the same" +
    //                         " company as the Point of Sale. You are probably trying" +
    //                         " to load the point of sale as and administrator in a" +
    //                         " multi-company setup, with the administrator account" +
    //                         " set to the wrong company."
    //                     ));
    //                 }
    //             }
    //         });
    //         this.models.push({
    //             model: "res.partner",
    //             fields: ["name", "data_alteracao", "whatsapp", "gender", "birthdate",
    //                 "number", "street2", "opt_out", "create_date", "cnpj_cpf", "street",
    //                 "city", "state_id", "country_id", "phone", "zip", "mobile", "email",
    //                 "ean13", "write_date", "debit", "credit", "credit_limit",
    //                 "users_ids", "city_id",
    //             ],
    //             domain: [["customer", "=", true]],
    //             loaded: function (self, partners) {
    //                 self.partners = partners;
    //                 self.db.partner_by_id = [];
    //                 self.db.partner_sorted = [];
    //                 self.db.add_partner(partners);
    //             }
    //         });
    //         this.models.push({
    //             model: "res.company",
    //             fields: ["ambiente_sat", "cnpj_cpf", "inscr_est", "currency_id",
    //                 "email", "website", "company_registry", "name", "phone",
    //                 "partner_id", "country_id", "tax_calculation_rounding_method",
    //             ],
    //             ids: function (self) {
    //                 return [self.user.company_id[0]];
    //             },
    //             loaded: function (self, companies) {
    //                 self.company = companies[0];
    //             }
    //         });
    //     },
    //     find_model: function (model_name) {
    //         var lookup = {};
    //         for (var i = 0; i < this.models.length; i++) {
    //             if (this.models[i].model == model_name) {
    //                 lookup[i] = self.models[i];
    //             }
    //         }
    //         return lookup;
    //     },
    //     cancel_pos_order: function (chave_cfe) {
    //         var posOrderModel = models.Order;
    //         var posOrder = posOrderModel.call("cancel_last_order", {
    //             "chave_cfe": chave_cfe
    //         })
    //             .then(function (orders) {
    //                 console.log("cancel_pos_order");
    //                 console.log(this);
    //                 this.pos_widget.screen_selector.show_popup("error", {
    //                     message: ("Venda cancelada!"),
    //                     comment: ("A venda foi cancelada com sucesso."),
    //                 });
    //             });
    //     },
    // });
});
