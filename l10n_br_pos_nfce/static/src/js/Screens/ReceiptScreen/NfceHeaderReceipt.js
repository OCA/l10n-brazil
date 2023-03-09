odoo.define("l10n_br_pos_nfce.NfceHeaderReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class NfceHeaderReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.order = this.props.receipt;
            this.company = this.props.company;
            this.companyAddress = this.props.company.address;
        }

        get companyCNPJ() {
            return this.company.vat;
        }

        get companyIE() {
            return this.company.inscr_est;
        }

        get fullCompanyAddress() {
            const {
                street_name,
                street_number,
                district,
                city,
                zip,
            } = this.companyAddress;
            return `${street_name}, ${street_number} - ${district} ${city}/UF - CEP: ${zip}`;
        }

        get companyLegalName() {
            return `${this.company.legal_name}`;
        }

        get isDocumentInContingency() {
            return !this.order.authorization_protocol;
        }
    }
    NfceHeaderReceipt.template = "NfceHeaderReceipt";

    Registries.Component.add(NfceHeaderReceipt);

    return {NfceHeaderReceipt};
});
