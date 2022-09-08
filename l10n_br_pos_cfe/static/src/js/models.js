/*
Copyright (C) 2022-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.models", function (require) {
    "use strict";
    const CFE_EMITIDO_COM_SUCESSO = "06000";
    const CFE_EMITIDO_COM_SUCESSO_MENSAGEM = "Autorizado o Uso do CF-e";
    const AMBIENTE_PRODUCAO = "producao";

    const SITUACAO_EDOC_REJEITADA = "rejeitada";
    const SITUACAO_EDOC_AUTORIZADA = "autorizada";

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
        // Initialize: function (attributes, options) {
        //     // CORE METHODS
        //     _super_order.initialize.apply(this, arguments, options);
        //     this.init_locked = true;

        //     this.init_locked = false;
        //     this.save_to_db();
        // },
        clone: function () {
            var order = _super_order.clone.call(this);
            // TODO: Verificar o que não deve ser copiado
            console.log("TODO: Verificar Order.clone l10n_br_pos_cfe");
            console.log(order);
            return order;
        },
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            // TODO: Verificar export_as_JSON l10n_br_pos_cfe

            console.log("TODO: Verificar Order.init_from_JSON l10n_br_pos_cfe");
            console.log(json);
        },
        _prepare_fiscal_json: function (json) {
            _super_order._prepare_fiscal_json.apply(this, arguments);

            var pos_config = this.pos.config;
            var pos_company = this.pos.company;

            if (pos_company.ambiente_sat === AMBIENTE_PRODUCAO) {
                json.company.cnpj = pos_company.cnpj_cpf;
                json.company.ie = pos_company.inscr_est;
                json.company.cnpj_software_house = pos_config.cnpj_software_house;
            } else {
                json.company.cnpj = pos_config.cnpj_homologacao;
                json.company.ie = pos_config.ie_homologacao;
                json.company.cnpj_software_house = pos_config.cnpj_software_house;
            }

            json.configs_sat = {};
            json.configs_sat.cnpj_software_house = json.company.cnpj_software_house;
            json.configs_sat.sat_path = pos_config.sat_path;
            json.configs_sat.numero_caixa = pos_config.numero_caixa;
            json.configs_sat.cod_ativacao = pos_config.cod_ativacao;
            json.configs_sat.impressora = pos_config.impressora;
            json.configs_sat.printer_params = pos_config.printer_params;
        },
        // Export_as_JSON: function () {
        //     var json = _super_order.export_as_JSON.apply(this, arguments);
        //     this._prepare_fiscal_json(json);
        //     return json;
        // },
        export_for_printing: function () {
            var json = _super_order.export_for_printing.apply(this, arguments);
            this._prepare_fiscal_json(json);
            return json;
        },
        _document_get_processor: function () {
            if (this.document_type === "59") {
                return this.pos.proxy.fiscal_device;
            }
            return _super_order._document_get_processor.call(this);
        },
        _document_check_result: async function (processor_result) {
            if (!this.document_type === "59") {
                return _super_order._document_check_result.call(this);
            }
            if (processor_result.successful && processor_result.response) {
                if (processor_result.response.EEEEE === CFE_EMITIDO_COM_SUCESSO) {
                    this._set_cfe_send_response(processor_result.response);
                    return true;
                }
                Gui.showPopup("ErrorPopup", {
                    title: this.pos.env._t("Falha ao emitir o CF-E"),
                    body: processor_result.response,
                });
            } else if (processor_result.traceback) {
                Gui.showPopup("ErrorTracebackPopup", processor_result.message);
            } else {
                Gui.showPopup("ErrorPopup", processor_result.message);
            }
            this.state_edoc = SITUACAO_EDOC_REJEITADA;
            return false;
        },
        _set_cfe_send_response: function (response) {
            this.set_document_session_number(response.numeroSessao);
            this.set_document_key(response.chaveConsulta);

            this.status_code = response.EEEEE;
            this.status_name = CFE_EMITIDO_COM_SUCESSO_MENSAGEM;
            this.status_description = response.mensagem;
            if (response.mensagemSEFAZ) {
                this.status_description =
                    this.status_description + "\n SEFAZ" + response.mensagemSEFAZ;
            }
            this.authorization_date = response.timeStamp;
            this.authorization_file = response.arquivoCFeSAT;
            this.document_qrcode_signature = response.assinaturaQRCODE;

            this.state_edoc = SITUACAO_EDOC_AUTORIZADA;

            // This.authorization_protocol =
            // processor_result.response.CCCC
            // processor_result.response.cod
            // processor_result.response.attributos
            // processor_result.response.valorTotalCFe
            // processor_result.response.CPFCNPJValue
            this.document_event_messages.push({
                id: 1005,
                label: CFE_EMITIDO_COM_SUCESSO_MENSAGEM,
            });
            this._document_status_popup();
            // TODO: Verificar se o horário no backend esta correto e a necesidade deste campo
            // this.fiscal_coupon_date = json_result.timeStamp.replace("T", " ");
        },
        _document_cancel_check_result: async function (result) {
            if (this.backendId === result.response.order_id) {
                this.cancel_file = result.response.xml;
                this.cancel_protocol_number = result.response.numeroSessao;
                this.cancel_document_key = result.response.chave_cfe;
                // FIXME: cancel_date
                // this.cancel_date =
            } else {
                Gui.showPopup("ErrorTracebackPopup", {
                    title: this.pos.env._t("Falha ao cancelar o CF-E"),
                    body: result.response,
                });
            }
            return _super_order._document_cancel_check_result.apply(this, arguments);
        },
        set_document_key: function (document_key) {
            this.document_key = document_key;
            // TODO: converter chave nos outros campos;
        },
        set_document_session_number: function (document_session_number) {
            this.pos.last_document_session_number = document_session_number;
            this.document_session_number = document_session_number;
        },
    });

    var _super_payment_line = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        _prepare_fiscal_json: function (json) {
            _super_payment_line._prepare_fiscal_json.apply(this, arguments);
            json.sat_payment_mode = this.payment_method.sat_payment_mode;
            json.sat_card_accrediting = this.payment_method.sat_card_accrediting;
        },
        // Export_as_JSON: function () {
        //     var json = _super_payment_line.export_as_JSON.apply(this, arguments);
        //     this._prepare_fiscal_json(json);
        //     return json;
        // },
        export_for_printing: function () {
            var json = _super_payment_line.export_for_printing.apply(this, arguments);
            this._prepare_fiscal_json(json);
            return json;
        },
    });
});
