/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos.models", function (require) {
    "use strict";
    const core = require("web.core");
    const utils = require("web.utils");
    const models = require("point_of_sale.models");
    const util = require("l10n_br_pos.util");
    const {Gui} = require("point_of_sale.Gui");

    const round_pr = utils.round_precision;
    const _t = core._t;

    const SITUACAO_EDOC_EM_DIGITACAO = "em_digitacao";
    const SITUACAO_EDOC_A_ENVIAR = "a_enviar";
    const SITUACAO_EDOC_ENVIADA = "enviada";
    const SITUACAO_EDOC_REJEITADA = "rejeitada";
    const SITUACAO_EDOC_AUTORIZADA = "autorizada";
    const SITUACAO_EDOC_CANCELADA = "cancelada";
    const SITUACAO_EDOC_DENEGADA = "denegada";
    const SITUACAO_EDOC_INUTILIZADA = "inutilizada";

    const SITUACAO_EDOC = {
        [SITUACAO_EDOC_EM_DIGITACAO]: "Em digitação",
        [SITUACAO_EDOC_A_ENVIAR]: "Aguardando envio",
        [SITUACAO_EDOC_ENVIADA]: "Aguardando processamento",
        [SITUACAO_EDOC_REJEITADA]: "Rejeitada",
        [SITUACAO_EDOC_AUTORIZADA]: "Autorizada",
        [SITUACAO_EDOC_CANCELADA]: "Cancelada",
        [SITUACAO_EDOC_DENEGADA]: "Denegada",
        [SITUACAO_EDOC_INUTILIZADA]: "Inutilizada",
    };

    const PARTNER_COMPANY_FIELDS = [
        "legal_name",
        "cnpj_cpf",
        "inscr_est",
        "inscr_mun",
        "suframa",
        "tax_framework",
        "street_number",
        "city_id",
        "street_name",
        "zip",
        "district",
    ];
    models.load_fields("res.partner", PARTNER_COMPANY_FIELDS.concat(["ind_ie_dest"]));
    models.load_fields("res.company", PARTNER_COMPANY_FIELDS.concat(["tax_framework", "logo"]));

    models.load_fields("uom.uom", ["code"]);

    models.load_fields("product.product", [
        "tax_icms_or_issqn",
        "fiscal_type",
        "icms_origin",
        "fiscal_genre_code",
        "ncm_id",
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
        fields: [],
        domain: function (self) {
            return [
                ["pos_config_id", "=", self.config.id],
                ["company_id", "=", (self.company && self.company.id) || false],
            ];
        },
        loaded: function (self, lines) {
            self.fiscal_map = lines;
            self.fiscal_map_by_template_id = {};
            lines.forEach((line) => { self.fiscal_map_by_template_id[line.product_tmpl_id[0]] = line; });
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.call(this, attributes, options);

            this.cnpj_cpf = "";

            this.fiscal_operation_id = this.pos.config.out_pos_fiscal_operation_id[0] || null;
            this.document_type_id = this.pos.config.simplified_document_type_id[0] || null;
            this.document_type = this.pos.config.simplified_document_type_id[1] || null;

            this.status_code = this.status_code || 0;
            this.status_description = this.status_description || "";
            this.state_edoc = this.state_edoc || SITUACAO_EDOC_EM_DIGITACAO;

            this.document_serie_number = this.document_serie_number || null;
            this.document_serie_id = this.document_serie || null;
            this.document_key = this.document_key || null;
            this.document_date = this.document_date || "";
            this.document_electronic = this.document_electronic || false;

            this.authorization_date = this.authorization_date || null;
            this.authorization_protocol = this.authorization_protocol || null;
            this.authorization_file = this.authorization_file || null;

            this.cancel_date = this.cancel_date || null;
            this.cancel_protocol_number = this.cancel_protocol_number || null;
            this.cancel_file = this.cancel_file || null;

            this.document_event_messages = this.document_event_messages || [];
        },
        
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.call(this, json);

            this.cnpj_cpf = json.cnpj_cpf;

            this.fiscal_operation_id = json.fiscal_operation_id;
            this.document_type_id = json.document_type_id;

            this.status_code = json.status_code;
            this.status_description = json.status_description;
            this.state_edoc = json.state_edoc;

            this.document_serie_number = json.document_number;
            this.document_serie_id = json.document_serie;
            this.document_key = json.document_key;
            this.document_date = json.document_date;
            this.document_electronic = json.document_electronic;

            this.authorization_date = json.authorization_date;
            this.authorization_protocol = json.authorization_protocol;
            this.authorization_file = json.authorization_file;

            this.cancel_date = json.cancel_date;
            this.cancel_protocol_number = json.cancel_protocol_number;
            this.cancel_file = json.cancel_file;

            this.document_event_messages = json.document_event_messages;
        },

        export_as_JSON: function () {
            const json = _super_order.export_as_JSON.call(this);

            json.cnpj_cpf = this.cnpj_cpf;

            json.fiscal_operation_id = this.fiscal_operation_id;
            json.document_type_id = this.document_type_id;

            json.status_code = this.status_code;
            json.status_description = this.status_description;
            json.state_edoc = this.state_edoc;

            json.document_number = this.document_number;
            json.document_serie = this.document_serie;
            json.document_key = this.document_key;
            json.document_date = this.document_date;
            json.document_electronic = this.document_electronic;

            json.authorization_date = this.authorization_date;
            json.authorization_protocol = this.authorization_protocol;
            json.authorization_file = this.authorization_file;

            json.cancel_date = this.cancel_date;
            json.cancel_protocol_number = this.cancel_protocol_number;
            json.cancel_file = this.cancel_file;

            json.document_event_messages = this.document_event_messages;

            json.lines = json.lines.filter(function (line) {
                 return line[2].price_subtotal !== 0 || line[2].qty !== 0;
            });
            json.paymentlines = this.paymentlines.filter(function (line) {
                 return line.payment_status !== "reversed";
            });
            return json;
        },

        // FISCAL METHODS
        set_cnpj_cpf: function (cnpj_cpf) {
            if (util.validate_cnpj_cpf(cnpj_cpf)) {
                this.assert_editable();
                this.cnpj_cpf = cnpj_cpf;
                this.trigger("change", this);
                return true;
            } else {
                this.show_invalid_cnpj_cpf_alert();
                return false;
            }
        },

        show_invalid_cnpj_cpf_alert() {
            Gui.showPopup("ErrorPopup", {
                title: _t("Invalid CNPJ/CPF"),
                body: _t("Please enter a valid CNPJ/CPF."),
            });
        },

        get_cnpj_cpf: function () {
            const client = this.get_client();
            const partner_vat = client && client.vat ? client.vat : null;
            return this.cnpj_cpf || partner_vat;
        },

        get_federal_state_taxes: function () {
            const order = this.pos.get_order();
            const rounding = this.pos.currency.rounding;
            const line = order.orderlines[0];
            const federalTaxes = this.calculate_federal_taxes(order, line, rounding);
            const stateTaxes = this.calculate_state_taxes(order, line, rounding);
            return {
                federal: federalTaxes,
                estadual: stateTaxes,
            }
        },

        calculate_federal_taxes: function (order, line, rounding) {
            const federalPercent = line.cofins_percent + line.pis_percent;
            const federalTotal = round_pr(order.total_paid * (federalPercent / 100), rounding);

            return {
                percent: federalPercent,
                total: federalTotal,
            }
        },

        calculate_state_taxes: function (order, line, rounding) {
            const statePercent = line.icms_percent;
            const stateTotal = round_pr(order.total_paid * (statePercent / 100), rounding);

            return {
                percent: statePercent,
                total: stateTotal,
            }
        },

        compute_message: function (templateString, taxes) {
            return templateString.replace("{taxes}", taxes);
        },

        _document_status_popup: function () {
            this.document_event_messages.map((element) => ({
                id: element.id,
                label: element.label,
                item: element.id,
            }));
            this.pos.showSelectionPopup(this.document_event_messages, "Document Status");
        },

        update_state_edoc: function (newState) {
            this.state_edoc = newState;
        },

        add_document_event_message: function (id, label) {
            this.document_event_messages.push({
                id: id,
                label: label,
            });
        },

        document_send: async function (component) {
            this.update_state_edoc(SITUACAO_EDOC_AUTORIZADA)
            return true;
        },

        _document_validate: async function () {
            return true;
        },

        _document_get_processor: async function () {
            return true;
        },

        _document_check_result: async function () {
            this.update_state_edoc(SITUACAO_EDOC_AUTORIZADA);
        },
        
        _document_cancel_validate: async function () {
            return true;
        },
        
        _document_cancel_check_result: async function () {
            this.update_state_edoc(SITUACAO_EDOC_CANCELADA);
        },
        
        document_cancel: async function (cancel_reason) {
            this.cancel_reason = cancel_reason;
            return true;
        },

        get_situacao_edoc: function () {
            return this.state_edoc ? SITUACAO_EDOC[this.state_edoc] : "";
        },

        cancel_order: function () {
            try {
                this.pos.rpc({
                    model: "pos.order",
                    method: "cancel_pos_order",
                    args: [{ "pos_reference": this.name }],
                });
            } catch (error) {
                this.pos.handle_offline_error(error);
            }
        },

        handle_offline_error: function (error) {
            if (
                error.message &&
                [100, 200, 404, -32098].includes(error.message.code)
            ) {
                Gui.showPopup("ErrorPopup", {
                    title: this.pos.comp.env._t("Network Error"),
                    body: this.pos.comp.env._t(
                        "Unable to update values in backend if offline."
                    ),
                });
                Gui.setSyncStatus("error");
            } else {
                throw error;
            }
        },

        decode_cancel_xml: function (XmlEncoded) {
            return decodeURIComponent(atob(XmlEncoded));
        },
    });

    const _super_payment_line = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        export_as_JSON: function () {
            const json = _super_payment_line.export_as_JSON.apply(this, arguments);
            json.payment_method = this.payment_method.edoc_payment_method;
            return json;
        },
    });

    const _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.cnpj_cpf = null;
            this.last_document_session_number = null;
            return _super_posmodel.initialize.call(this, session, attributes);
        },
    
        get_cnpj_cpf: function () {
            const order = this.get_order();
            return order ? order.get_cnpj_cpf() : "";
        },

        showSelectionPopup: function (list, title) {
            Gui.showPopup("SelectionPopup", {
                title: title,
                list: list,
                confirmText: "Confirm",
                cancelText: "Cancel",
            });
        },
    });

    return {
        models: models,
    }
});
