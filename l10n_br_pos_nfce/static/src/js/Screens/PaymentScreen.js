/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_nfce.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosNFCePaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            toggleIsToInvoice() {
                if (!this.document_type === "65") {
                    super.toggleIsToInvoice();
                }
            }
        };
    Registries.Component.extend(PaymentScreen, L10nBrPosNFCePaymentScreen);

    return L10nBrPosNFCePaymentScreen;
});
