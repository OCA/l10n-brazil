import {Component} from "@odoo/owl";

export class NfceHeaderReceipt extends Component {
    static template = "l10n_br_pos_nfce.NfceHeaderReceipt";
    static props = {receipt: Object};

    setup() {
        this.order = this.props.receipt;
        this.company = this.order.company;
        this.companyAddress = this.company.address;
    }

    get companyCNPJ() {
        return this.company.vat;
    }

    get companyIE() {
        return this.company.inscr_est;
    }

    get fullCompanyAddress() {
        const {street_name, street_number, district, city, zip, state} =
            this.companyAddress;

        return `${street_name}, ${street_number} - ${district} ${city}/${state} - CEP: ${zip}`;
    }

    get companyLegalName() {
        return this.company.legal_name;
    }

    get isDocumentInContingency() {
        return !this.order.authorization_protocol;
    }
}
