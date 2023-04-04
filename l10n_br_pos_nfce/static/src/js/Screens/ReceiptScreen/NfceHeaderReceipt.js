odoo.define("l10n_br_pos_nfce.NfceHeaderReceipt", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    const BRAZILIAN_STATES_MAP = {
        "Acre (BR)": "AC",
        "Alagoas (BR)": "AL",
        "Amazonas (BR)": "AM",
        "Amapá (BR)": "AP",
        "Bahia (BR)": "BA",
        "Ceará (BR)": "CE",
        "Distrito Federal (BR)": "DF",
        "Espírito Santo (BR)": "ES",
        "Goiás (BR)": "GO",
        "Maranhão (BR)": "MA",
        "Minas Gerais (BR)": "MG",
        "Mato Grosso do Sul (BR)": "MS",
        "Mato Grosso (BR)": "MT",
        "Pará (BR)": "PA",
        "Paraíba (BR)": "PB",
        "Pernambuco (BR)": "PE",
        "Piauí (BR)": "PI",
        "Paraná (BR)": "PR",
        "Rio de Janeiro (BR)": "RJ",
        "Rio Grande do Norte (BR)": "RN",
        "Rondônia (BR)": "RO",
        "Roraima (BR)": "RR",
        "Rio Grande do Sul (BR)": "RS",
        "Santa Catarina (BR)": "SC",
        "Sergipe (BR)": "SE",
        "São Paulo (BR)": "SP",
        "Tocantins (BR)": "TO",
    };

    class NfceHeaderReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this.order = this.props.receipt;
            this.company = this.props.company;
            this.companyAddress = this.props.company.address;
        }

        get companyCNPJ() {
            return this.company.cnpj_cpf;
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
                state,
            } = this.companyAddress;
            return `${street_name}, ${street_number} - ${district} ${city}/${BRAZILIAN_STATES_MAP[state]} - CEP: ${zip}`;
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
