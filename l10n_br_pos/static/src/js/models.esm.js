/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
@author: Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {PosStore} from "@point_of_sale/app/store/pos_store";
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

const getFirst = (val) => (Array.isArray(val) ? val[0] : val);

patch(PosStore.prototype, {
    async processServerData() {
        await super.processServerData(...arguments);
        const fiscalMapData = this.models["l10n_br_pos.product_fiscal_map"]
            ? this.models["l10n_br_pos.product_fiscal_map"].getAll()
            : [];
        this.fiscal_map_by_template_id = {};
        for (const line of fiscalMapData) {
            if (line.product_tmpl_id) {
                this.fiscal_map_by_template_id[getFirst(line.product_tmpl_id)] = line;
            }
        }
    },
});

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        // The fiscal fields are declared in the python model: only the
        // defaults of an order created by the PoS are set here.
        this.state_edoc = this.state_edoc || "em_digitacao";
        this.cnpj_cpf = this.cnpj_cpf || null;
        this.document_event_messages = this.document_event_messages || [];

        if (!vals.id) {
            const config = this.config;

            this.fiscal_operation_id =
                this.fiscal_operation_id ||
                getFirst(config.out_pos_fiscal_operation_id) ||
                null;
            this.document_type_id =
                this.document_type_id ||
                getFirst(config.simplified_document_type_id) ||
                null;
            this.document_type =
                this.document_type || config.simplified_document_type || null;
        }
    },

    get_cnpj_cpf() {
        const partner = this.get_partner();
        return this.cnpj_cpf || (partner ? partner.vat : null);
    },

    set_cnpj_cpf(cnpj_cpf) {
        if (validate_cnpj_cpf(cnpj_cpf)) {
            this.cnpj_cpf = cnpj_cpf;
            return true;
        }
        return false;
    },

    get_situacao_edoc() {
        return SITUACAO_EDOC[this.state_edoc] || "";
    },

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
    },
});
