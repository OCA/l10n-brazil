/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.ReprintReceiptScreen", function (require) {
    "use strict";

    const ReprintReceiptScreen = require("point_of_sale.ReprintReceiptScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosCfeReprintReceiptScreen = (
        ReprintReceiptScreen_screen = ReprintReceiptScreen
    ) =>
        class extends ReprintReceiptScreen_screen {
            async printReceipt() {
                setTimeout(() => super.printReceipt(), 1000);
            }
        };

    Registries.Component.extend(ReprintReceiptScreen, L10nBrPosCfeReprintReceiptScreen);

    return L10nBrPosCfeReprintReceiptScreen;
});
