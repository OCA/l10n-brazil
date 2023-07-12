/*
Copyright (C) 2022-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos.OrderRow", function (require) {
    "use strict";

    const OrderRow = require("point_of_sale.OrderRow");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosOrderRow = (OrderRow_screen = OrderRow) =>
        class extends OrderRow_screen {
            get document_serie_number() {
                if (
                    this.props.order.document_serie &&
                    this.props.order.document_number
                ) {
                    return (
                        this.props.order.document_type +
                        "/" +
                        this.props.order.document_serie +
                        "/" +
                        this.props.order.document_number
                    );
                }
                return null;
            }
            get customer() {
                const customer = this.order.get("client");
                const cnpj_cpf = this.props.order.get_cnpj_cpf();
                if (customer || cnpj_cpf) {
                    return (customer.name || "N/A") + " (" + cnpj_cpf + ")";
                }
                return null;
            }
            get edoc_state() {
                return this.props.order.get_situacao_edoc();
            }
        };

    Registries.Component.extend(OrderRow, L10nBrPosOrderRow);

    return L10nBrPosOrderRow;
});
