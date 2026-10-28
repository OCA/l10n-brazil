/** @odoo-module */

import {Component} from "@odoo/owl";
import {NfceFiscalInfoReceipt} from "@l10n_br_pos_nfce/js/Screens/ReceiptScreen/NfceFiscalInfoReceipt.esm";
import {NfceFooterReceipt} from "@l10n_br_pos_nfce/js/Screens/ReceiptScreen/NfceFooterReceipt.esm";
import {NfceHeaderReceipt} from "@l10n_br_pos_nfce/js/Screens/ReceiptScreen/NfceHeaderReceipt.esm";
import {NfceItemReceipt} from "@l10n_br_pos_nfce/js/Screens/ReceiptScreen/NfceItemReceipt.esm";
import {NfcePaymentlineReceipt} from "@l10n_br_pos_nfce/js/Screens/ReceiptScreen/NfcePaymentlineReceipt.esm";
import {NfceTotalsReceipt} from "@l10n_br_pos_nfce/js/Screens/ReceiptScreen/NfceTotalsReceipt.esm";
import {OrderReceipt} from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

export class NfceOrderReceipt extends Component {
    static template = "l10n_br_pos_nfce.NfceOrderReceipt";
    static components = {
        NfceHeaderReceipt,
        NfceItemReceipt,
        NfceTotalsReceipt,
        NfcePaymentlineReceipt,
        NfceFiscalInfoReceipt,
        NfceFooterReceipt,
    };
    static props = {data: Object};

    get receipt() {
        return this.props.data;
    }

    get isHomologationEnvironment() {
        return this.receipt.nfce_environment === "2";
    }

    get hasChange() {
        return this.receipt.change;
    }

    get orderChange() {
        return this.receipt.change.toLocaleString("pt-br", {
            minimumFractionDigits: 2,
        });
    }
}

// The standard receipt (screen, printer, e-mail) renders the NFC-e layout
// when the exported data is flagged as NFC-e.
Object.assign(OrderReceipt.components, {NfceOrderReceipt});
