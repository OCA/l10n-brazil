/** @odoo-module **/

/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
@author: Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

import {Order, Orderline, Paymentline, PosGlobalState} from "point_of_sale.models";
import {Gui} from "point_of_sale.Gui";
import Registries from "point_of_sale.Registries";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {validate_cnpj_cpf} from "@l10n_br_pos/js/util.esm";

const SITUACAO_EDOC = {
    em_digitacao: "Em digitação",
    a_enviar: "Aguardando envio",
    enviada: "Aguardando processamento",
    rejeitada: "Rejeitada",
    autorizada: "Autorizada",
    cancelada: "Cancelada",
    denegada: "Denegada",
    inutilizada: "Inutilizada",
};

if (PosGlobalState) {
    patch(PosGlobalState.prototype, "l10n_br_pos.PosGlobalState", {
        async _load_server_data() {
            const result = await super._load_server_data(...arguments);
            const fiscalMapData = this.models["l10n_br_pos.product_fiscal_map"] || [];
            this.fiscal_map_by_template_id = {};
            for (const line of fiscalMapData) {
                if (line.product_tmpl_id) {
                    const tmplId = Array.isArray(line.product_tmpl_id)
                        ? line.product_tmpl_id[0]
                        : line.product_tmpl_id;
                    this.fiscal_map_by_template_id[tmplId] = line;
                }
            }
            return result;
        },
    });
}

const L10nBrOrder = (BaseOrder) =>
    class extends BaseOrder {
        setup(_default_attributes, options) {
            super.setup(...arguments);
            this.state_edoc = this.state_edoc || "em_digitacao";
            this.cnpj_cpf = this.cnpj_cpf || null;
            // Always ensure the array exists
            this.document_event_messages = [];

            if (!options || !options.json) {
                const config = this.pos.config;
                const getFirst = (val) => (Array.isArray(val) ? val[0] : val);

                this.fiscal_operation_id =
                    getFirst(config.out_pos_fiscal_operation_id) || null;
                this.document_type_id =
                    getFirst(config.simplified_document_type_id) || null;
                this.document_type = config.simplified_document_type || null;
            }
        }

        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            // Re-initialize array when loading from JSON
            this.document_event_messages = json.document_event_messages || [];
            Object.assign(this, {
                state_edoc: json.state_edoc || "em_digitacao",
                cnpj_cpf: json.cnpj_cpf || null,
                document_key: json.document_key || null,
                document_number: json.document_number || null,
                document_serie: json.document_serie || null,
                fiscal_operation_id: json.fiscal_operation_id || null,
                document_type_id: json.document_type_id || null,
                document_type: json.document_type || null,
            });
        }

        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            if (json.lines) {
                json.lines = json.lines.filter(
                    (l) => l.qty !== 0 || l.price_unit !== 0
                );
            }
            Object.assign(json, {
                state_edoc: this.state_edoc,
                cnpj_cpf: this.get_cnpj_cpf(),
                document_key: this.document_key,
                document_number: this.document_number,
                document_serie: this.document_serie,
                fiscal_operation_id: this.fiscal_operation_id,
                document_type_id: this.document_type_id,
                document_type: this.document_type,
                document_event_messages: this.document_event_messages,
            });
            return json;
        }

        get_cnpj_cpf() {
            const partner = this.get_partner();
            return this.cnpj_cpf || (partner ? partner.vat : null);
        }

        set_cnpj_cpf(cnpj_cpf) {
            if (validate_cnpj_cpf(cnpj_cpf)) {
                this.cnpj_cpf = cnpj_cpf;
                return true;
            }
            Gui.showPopup("ErrorPopup", {
                title: _t("CNPJ / CPF Inválido !"),
                body: _t("Insira um número de CNPJ / CPF válido"),
            });
            return false;
        }

        get_situacao_edoc() {
            return SITUACAO_EDOC[this.state_edoc] || "";
        }

        async document_send() {
            if (!this.document_event_messages) {
                this.document_event_messages = [];
            }
            this.document_event_messages.push({
                id: 1000,
                label: "Iniciando Transmissão",
            });
            this.state_edoc = "a_enviar";
            return true;
        }
    };

if (Order) {
    Registries.Model.extend(Order, L10nBrOrder);
}

const L10nBrOrderline = (BaseOrderline) =>
    class extends BaseOrderline {
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            const product = this.get_product();
            const fiscalMap = this.pos.fiscal_map_by_template_id
                ? this.pos.fiscal_map_by_template_id[product.product_tmpl_id]
                : false;

            if (fiscalMap) {
                Object.assign(json, {
                    cfop: fiscalMap.cfop_code,
                    icms_cst_code: fiscalMap.icms_cst_code,
                    icms_percent: fiscalMap.icms_percent,
                    ncm:
                        fiscalMap.ncm_code === "00000000"
                            ? "99999999"
                            : fiscalMap.ncm_code,
                });
            }
            return json;
        }
    };

if (Orderline) {
    Registries.Model.extend(Orderline, L10nBrOrderline);
}

const L10nBrPaymentline = (BasePaymentline) =>
    class extends BasePaymentline {
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.payment_status = this.payment_status;
            return json;
        }
    };

if (Paymentline) {
    Registries.Model.extend(Paymentline, L10nBrPaymentline);
}
