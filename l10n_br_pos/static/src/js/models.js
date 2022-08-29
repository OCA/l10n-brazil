/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos.models", function (require) {
    "use strict";
    const core = require("web.core");
    const rpc = require("web.rpc");
    const _t = core._t;

    const utils = require("web.utils");
    const round_pr = utils.round_precision;

    var models = require("point_of_sale.models");
    var util = require("l10n_br_pos.util");
    var partner_company_fields = [
        "legal_name",
        "cnpj_cpf",
        "inscr_est",
        "inscr_mun",
        "suframa",
        "tax_framework",
        "street_number",
        "city_id",
    ];
    models.load_fields("res.partner", partner_company_fields.concat(["ind_ie_dest"]));
    models.load_fields("res.company", partner_company_fields.concat(["tax_framework"]));
    models.load_fields("uom.uom", ["code"]);
    models.load_fields("product.product", [
        "tax_icms_or_issqn",
        "fiscal_type",
        "icms_origin",
        "fiscal_genre_code",
        "ncm_id",
        // FIXME: Verificar o que houve.
        // "ncm_code",
        // "ncm_code_exception",
        "nbm_id",
        "fiscal_genre_id",
        "service_type_id",
        "city_taxation_code_id",
        "ipi_guideline_class_id",
        "ipi_control_seal_id",
        "nbs_id",
        "cest_id",
    ]);

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
            return [
                ["pos_config_id", "=", self.config.id],
                ["company_id", "=", (self.company && self.company.id) || false],
            ];
        },
        loaded: function (self, lines) {
            self.fiscal_map = lines;
            self.fiscal_map_by_template_id = {};
            lines.forEach(function (line) {
                self.fiscal_map_by_template_id[line.product_tmpl_id[0]] = line;
            });
        },
    });

    models.load_models({
        model: "pos.order",
        fields: [
            "name",
            "partner_id",
            "date_order",
            "fiscal_coupon_date",
            "amount_total",
            "pos_reference",
            "lines",
            "state",
            "session_id",
            "company_id",
            "document_key",
            "cnpj_cpf",
            "cancel_document_key",
        ],
        domain: function () {
            var domain = [
                ["state", "in", ["paid", "done"]],
                ["amount_total", ">", 0],
            ];
            return domain;
        },
        loaded: function (self, orders) {
            self.paid_orders = orders;
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments, options);
            this.init_locked = true;

            this.cnpj_cpf = this.cnpj_cpf || null;
            this.document_authorization_date = this.document_authorization_date || null;
            this.document_status_code = this.document_status_code || null;
            this.document_status_name = this.document_status_name || null;
            this.document_session_number = this.document_session_number || null;
            this.document_key = this.document_key || null;
            this.document_file = this.document_file || null;
            this.fiscal_coupon_date = this.fiscal_coupon_date || null;

            if (options.json) {
                this.init_from_JSON(options.json);
            } else {
                this.fiscal_operation_id = this.pos.config.out_pos_fiscal_operation_id[0];
                this.document_type_id = this.pos.config.simplified_document_type_id[0];
                this.document_type = this.pos.config.simplified_document_type;
            }

            this.init_locked = false;
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
            this.fiscal_coupon_date = json_result.timeStamp.replace("T", " ");
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
            if (util.validate_cnpj_cpf(cnpj_cpf)) {
                this.assert_editable();
                this.cnpj_cpf = cnpj_cpf;
                this.trigger("change", this);
                return true;
            }
            this.pos.gui.show_popup("alert", {
                title: _t("Invalid CNPJ / CPF !"),
                body: _t("Enter a valid CNPJ / CPF number"),
            });
            return false;
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
            json.fiscal_coupon_date = this.fiscal_coupon_date;
            return json;
        },
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.cnpj_cpf = json.cnpj_cpf;
            this.fiscal_operation_id = json.fiscal_operation_id;
            this.document_type = json.document_type;
            this.document_type_id = json.document_type_id;
        },
        get_taxes_and_percentages: function (order) {
            var taxes = {
                federal: {
                    percent: 0,
                    total: 0,
                },
                estadual: {
                    percent: 0,
                    total: 0,
                },
            };
            const rounding = this.pos.currency.rounding;
            var line = order.orderlines[0];
            taxes.federal.percent = line.cofins_percent + line.pis_percent;
            taxes.federal.total = round_pr(
                order.total_paid * (taxes.federal.percent / 100),
                rounding
            );
            taxes.estadual.percent = line.icms_percent;
            taxes.estadual.total = round_pr(
                order.total_paid * (taxes.estadual.percent / 100),
                rounding
            );

            return taxes;
        },
        fillTemplate: function (templateString, taxes) {
            return new Function(`return \`${templateString}\`;`).call(this, taxes);
        },
        export_for_printing: function () {
            var result = _super_order.export_for_printing.apply(this, arguments);
            result.orderlines = _.filter(result.orderlines, function (line) {
                return line.price !== 0;
            });
            var company = this.pos.company;

            result.company = {};
            result.configs_sat = {};
            result.pos_session_id = this.pos.pos_session.id;
            result.client = this.get_cnpj_cpf();

            result.company.cnpj = company.cnpj;
            result.company.ie = company.ie;
            result.company.tax_framework = company.tax_framework;

            if (this.pos.config.additional_data) {
                var taxes = this.get_taxes_and_percentages(result);
                result.additional_data = this.fillTemplate(
                    this.pos.config.additional_data,
                    taxes
                );
            }

            return result;
        },
        //        Add_product: function (product) {
        //            Const product_fiscal_map = this.pos.fiscal_map_by_template_id[
        //                product.product_tmpl_id
        //            ];
        //            If (!product_fiscal_map) {
        //                this.pos.gui.show_popup("alert", {
        //                    title: _t("Tax Details"),
        //                    body: _t(
        //                        "There was a problem mapping the item tax. Please contact support."
        //                    ),
        //                });
        //            } else if (!product_fiscal_map.fiscal_operation_line_id) {
        //                this.pos.gui.show_popup("alert", {
        //                    title: _t("Fiscal Operation Line"),
        //                    body: _t(
        //                        "The fiscal operation line is not defined for this product. Please contact support."
        //                    ),
        //                });
        //            } else {
        //            }
        //            _super_order.add_product.apply(this, arguments);
        //        },
        push_new_order_list: async function () {
            return new Promise(function (resolve, reject) {
                rpc.query({
                    model: "pos.order",
                    method: "search_read",
                    args: [
                        [
                            ["state", "in", ["paid", "done"]],
                            ["amount_total", ">", 0],
                        ],
                    ],
                    limit: 40,
                }).then(
                    function (orders) {
                        //                        Posmodel.paid_orders = orders;
                        self.paid_orders = orders;
                        resolve(true);
                    },
                    (error) => {
                        reject(error);
                    }
                );
            });
        },
    });

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function () {
            var result = _super_order_line.export_for_printing.apply(this, arguments);
            var self = this;
            var product = this.get_product();
            var product_fiscal_map =
                self.pos.fiscal_map_by_template_id[product.product_tmpl_id];

            result.additional_data = product_fiscal_map.additional_data || "";
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
            result.ncm =
                product_fiscal_map.ncm_code === "00000000"
                    ? "99999999"
                    : product_fiscal_map.ncm_code;
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

    //    Var _super_posmodel = models.PosModel.prototype;

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
});
