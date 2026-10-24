/** @odoo-module **/

/*
Copyright (C) 2026-Today Escodoo (https://www.escodoo.com.br)
@author: Kaynnan Lemes kaynnan.lemes@escodoo.com.br
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

import {TicketScreen} from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(TicketScreen.prototype, {
    /**
     * Returns the formatted fiscal document string.
     * @param {Object} order The PoS Order.
     * @returns {String} Formatted document type/serie/number.
     */
    getDocumentSerieNumber(order) {
        if (!order) {
            return "";
        }
        if (order.document_serie && order.document_number) {
            const dt = order.document_type || "";
            return `${dt}/${order.document_serie}/${order.document_number}`;
        }
        return "";
    },

    /**
     * Returns the e-doc situation.
     * @param {Object} order The PoS Order.
     * @returns {String} Current e-doc state label.
     */
    getEdocState(order) {
        if (!order) {
            return "";
        }
        return order.get_situacao_edoc
            ? order.get_situacao_edoc()
            : order.state_edoc || "";
    },

    /**
     * Returns formatted customer info.
     * @param {Object} order The PoS Order.
     * @returns {String} Partner name and CNPJ/CPF.
     */
    getCustomer(order) {
        const partner = order && order.get_partner ? order.get_partner() : null;
        const cnpj_cpf = order && order.get_cnpj_cpf ? order.get_cnpj_cpf() : null;

        if (partner || cnpj_cpf) {
            return `${partner ? partner.name : "N/A"} (${cnpj_cpf || ""})`;
        }
        return "";
    },

    /**
     * @override
     */
    _getSearchFields() {
        return Object.assign({}, super._getSearchFields(...arguments), {
            FISCAL_DOCUMENT: {
                repr: (order) => this.getDocumentSerieNumber(order),
                displayName: _t("Documento Fiscal"),
                modelField: "document_number",
            },
        });
    },
});
