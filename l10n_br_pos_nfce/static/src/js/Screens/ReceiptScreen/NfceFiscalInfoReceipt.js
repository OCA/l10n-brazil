odoo.define("l10n_br_pos_nfce.NfceFiscalInfoReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class NfceFiscalInfoReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.order = this.props.receipt;
        }

        get documentKeyFormatted() {
            return this.order.document_key.replace(/(.{4})/g, "$1 ");
        }

        get urlConsulta() {
            return this.order.url_consulta;
        }
    }
    NfceFiscalInfoReceipt.template = "NfceFiscalInfoReceipt";

    Registries.Component.add(NfceFiscalInfoReceipt);

    return {NfceFiscalInfoReceipt};
});
