/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.ReceiptScreen", function (require) {
    "use strict";

    const ReceiptScreen = require("point_of_sale.ReceiptScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosCfeReceiptScreen = (ReceiptScreen_screen = ReceiptScreen) =>
        class extends ReceiptScreen_screen {
            // @override
            async handleAutoPrint() {
                if (this._shouldAutoPrint()) {
                    setTimeout(() => this.cfePrinting(), 1000);
                }
            }
            async cfePrinting() {
                await this.printReceipt();
                if (this.currentOrder._printed && this._shouldCloseImmediately()) {
                    this.whenClosing();
                }
            }
        };

    Registries.Component.extend(ReceiptScreen, L10nBrPosCfeReceiptScreen);

    return L10nBrPosCfeReceiptScreen;
});
