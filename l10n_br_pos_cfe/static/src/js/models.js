/*
Copyright (C) 2022-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.models", function (require) {
    "use strict";

    const AMBIENTE_PRODUCAO = "producao";

    var models = require("point_of_sale.models");
    const {Gui} = require("point_of_sale.Gui");

    var _config = _.findWhere(models.PosModel.prototype.models, {model: "pos.config"});
    var old_loaded = _config.loaded;
    _config.loaded = function (self, configs) {
        old_loaded(self, configs);
        if (self.config.iface_fiscal_via_proxy) {
            self.config.use_proxy = true;
        }
    };

    models.load_fields("res.company", [
        "ambiente_sat",
        "cnpj_software_house",
        "sign_software_house",
    ]);
    models.load_fields("pos.payment.method", [
        "sat_payment_mode",
        "sat_card_accrediting",
    ]);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            // CORE METHODS
            _super_order.initialize.apply(this, arguments, options);
            this.init_locked = true;

            if (options.json) {
                console.log("");
            } else {
                console.log("");
            }

            this.init_locked = false;
            this.save_to_db();
        },
        clone: function () {
            var order = _super_order.clone.call(this);
            // TODO: Verificar o que não deve ser copiado
            console.log("TODO: Verificar Order.clone l10n_br_pos_cfe");
            console.log(order);
            return order;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.call(this);
            // TODO: Verificar export_as_JSON l10n_br_pos_cfe
            console.log("TODO: Verificar Order.export_as_JSON l10n_br_pos_cfe");
            console.log(json);
            return json;
        },
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            // TODO: Verificar export_as_JSON l10n_br_pos_cfe
            console.log("TODO: Verificar Order.init_from_JSON l10n_br_pos_cfe");
            console.log(json);
        },
        export_for_printing: function () {
            var result = _super_order.export_for_printing.apply(this, arguments);
            var pos_config = this.pos.config;
            var pos_company = this.pos.company;

            if (pos_company.ambiente_sat === AMBIENTE_PRODUCAO) {
                result.company.cnpj = pos_company.cnpj_cpf;
                result.company.ie = pos_company.inscr_est;
                result.company.cnpj_software_house = pos_config.cnpj_software_house;
            } else {
                result.company.cnpj = pos_config.cnpj_homologacao;
                result.company.ie = pos_config.ie_homologacao;
                result.company.cnpj_software_house = pos_config.cnpj_software_house;
            }

            result.configs_sat = {};
            result.configs_sat.cnpj_software_house = result.company.cnpj_software_house;
            result.configs_sat.sat_path = pos_config.sat_path;
            result.configs_sat.numero_caixa = pos_config.numero_caixa;
            result.configs_sat.cod_ativacao = pos_config.cod_ativacao;
            result.configs_sat.impressora = pos_config.impressora;
            result.configs_sat.printer_params = pos_config.printer_params;

            return result;
        },
        _document_get_processor: function () {
            if (this.document_type == "59") {
                return this.pos.proxy.fiscal_device;
            }
            return _super_order._document_get_processor.call(this);
        },
        _document_check_result: async function (processor_result) {
            if (!this.document_type == "59") {
                return _super_order._document_check_result.call(this);
            }
            if (processor_result.successful) {
                this.document_event_messages.push({
                    id: 1005,
                    label: processor_result.message,
                });
                // TODO: Processar a resposta com sucesso;
                this._document_status_popup();
                return true;
            } else {
                if (processor_result.traceback){
                    Gui.showPopup('ErrorTracebackPopup', processor_result.message);
                } else {
                    Gui.showPopup('ErrorPopup', processor_result.message);
                }
            }
            return false;
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
    });

    var _super_payment_line = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        export_for_printing: function () {
            var result = _super_payment_line.export_for_printing.apply(this, arguments);
            result.sat_payment_mode = this.payment_method.sat_payment_mode;
            result.sat_card_accrediting = this.payment_method.sat_card_accrediting;
            return result;
        },
        export_as_JSON: function () {
            var result = _super_payment_line.export_as_JSON.apply(this, arguments);
            result.sat_payment_mode = this.payment_method.sat_payment_mode;
            result.sat_card_accrediting = this.payment_method.sat_card_accrediting;
            return result;
        },
    });
});
