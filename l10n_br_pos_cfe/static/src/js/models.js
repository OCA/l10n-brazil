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
    const SITUACAO_EDOC_CANCELADA = "cancelada";

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
        "environment_sat",
        "cnpj_software_house",
        "sign_software_house",
    ]);
    models.load_fields("pos.payment.method", ["sat_payment_mode", "sat_card_acquirer"]);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        // TODO: Verificar o que não deve ser copiado através do clone
        // TODO: Verificar o funcionamento do export_as_JSON
        _prepare_fiscal_json: function (json) {
            _super_order._prepare_fiscal_json.apply(this, arguments);

            var pos_config = this.pos.config;
            var pos_company = this.pos.company;

            json.company.name = pos_company.name;
            json.company.legal_name = pos_company.legal_name;
            json.company.address = {
                street_name: pos_company.street_name,
                street_number: pos_company.street_number,
                district: pos_company.district,
                city: pos_company.city_id[1],
                zip: pos_company.zip,
            };
            json.company.inscr_mun = pos_company.inscr_mun;
            json.rounding = this.pos.currency.rounding;

            if (pos_company.sat_environment === AMBIENTE_PRODUCAO) {
                json.company.cnpj = pos_company.cnpj_cpf;
                json.company.ie = pos_company.inscr_est;
                json.company.cnpj_software_house = pos_config.cnpj_software_house;
            } else {
                json.company.cnpj = pos_config.cnpj_homologation;
                json.company.ie = pos_config.ie_homologation;
                json.company.cnpj_software_house = pos_config.cnpj_software_house;
            }

            if (json.cnpj_cpf) {
                json.client = json.cnpj_cpf
                    .replace(".", "")
                    .replace(".", "")
                    .replace("-", "")
                    .replace("/", "");
            }

            json.configs_sat = {};
            json.configs_sat.cnpj_software_house = json.company.cnpj_software_house;
            json.configs_sat.sat_path = pos_config.sat_path;
            json.configs_sat.numero_caixa = pos_config.cashier_number;
            json.configs_sat.cod_ativacao = pos_config.activation_code;
            json.configs_sat.impressora = pos_config.printer;
            json.configs_sat.printer_params = pos_config.printer_params;
        },
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

            const document_key = response.chaveConsulta.replace("CFe", "");
            this.set_document_number(document_key);
            this.set_document_serie(document_key);

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

            this.document_event_messages.push({
                id: 1005,
                label: CFE_EMITIDO_COM_SUCESSO_MENSAGEM,
            });
            this._document_status_popup();
            // TODO: Verificar se o horário no backend esta correto e a necesidade deste campo
            // this.fiscal_coupon_date = json_result.timeStamp.replace("T", " ");
        },
        _document_cancel_check_result: async function (result) {
            if (!this.document_type === "59") {
                return _super_order._document_cancel_check_result.apply(
                    this,
                    arguments
                );
            }
            if (
                result &&
                result.successful &&
                this.backendId === result.response.order_id
            ) {
                this._set_cfe_cancel_response(result);

                return result;
            }
            Gui.showPopup("ErrorTracebackPopup", {
                title: this.pos.env._t("Falha ao cancelar o CF-E"),
                body: result.response,
            });

            return false;
        },
        _set_cfe_cancel_response: function (result) {
            const XmlDecoded = this.decode_cancel_xml(result.response.xml);
            const parser = new DOMParser();
            const doc = parser.parseFromString(XmlDecoded, "application/xml");
            const hEmi = doc.querySelector("ide>hEmi").innerHTML;
            const dEmi = doc.querySelector("ide>dEmi").innerHTML;
            const cancel_date = `${dEmi.substring(0, 4)}-${dEmi.substring(
                4,
                6
            )}-${dEmi.substring(6, 8)}T${hEmi.substring(0, 2)}:${hEmi.substring(
                2,
                4
            )}:${hEmi.substring(4, 6)}`;
            this.cancel_date = cancel_date;
            this.cancel_file = result.response.xml;
            this.cancel_protocol_number = result.response.numSessao;
            this.cancel_document_key = result.response.chave_cfe;
            this.cancel_qrcode_signature = doc.querySelector(
                "assinaturaQRCODE"
            ).innerHTML;
            this.state_edoc = SITUACAO_EDOC_CANCELADA;
        },
        set_document_key: function (document_key) {
            this.document_key = document_key;
            // TODO: converter chave nos outros campos;
        },
        set_document_session_number: function (document_session_number) {
            this.pos.last_document_session_number = document_session_number;
            this.document_session_number = document_session_number;
        },
        set_document_number: function (document_key) {
            this.document_number = document_key.substring(31, 37);
        },
        set_document_serie: function (document_key) {
            this.document_serie = document_key.substring(22, 31);
        },
    });

    var _super_payment_line = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        _prepare_fiscal_json: function (json) {
            _super_payment_line._prepare_fiscal_json.apply(this, arguments);
            json.sat_payment_mode = this.payment_method.sat_payment_mode || "";
            json.sat_card_accrediting = this.payment_method.sat_card_acquirer || "";
        },
        export_for_printing: function () {
            var json = _super_payment_line.export_for_printing.apply(this, arguments);
            return json;
        },
    });

    const _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function () {
            const json = _super_orderline.export_for_printing.call(this);
            this._prepare_fiscal_json(json);
            return json;
        },
    });
});
