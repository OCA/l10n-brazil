/** @odoo-module **/

/*
Copyright (C) 2026-Today Escodoo (https://www.escodoo.com.br)
@author: Kaynnan Lemes kaynnan.lemes@escodoo.com.br
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

import Registries from "point_of_sale.Registries";
import TicketScreen from "point_of_sale.TicketScreen";
import {_t} from "@web/core/l10n/translation";

export const TicketScreenPatch = (OriginalTicketScreen) =>
    class extends OriginalTicketScreen {
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
        }

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
        }

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
        }

        /**
         * @override
         */
        get _searchFields() {
            const fields = super._searchFields;
            return Object.assign({}, fields, {
                [_t("Documento Fiscal")]: (order) => this.getDocumentSerieNumber(order),
            });
        }
    };

Registries.Component.extend(TicketScreen, TicketScreenPatch);

export default TicketScreen;
