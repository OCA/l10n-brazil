/*
    Copyright (C) 2016-Today KMEE (https://kmee.com.br)
    @author: Luis Felipe Mileo <mileo@kmee.com.br>
    @author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
    @author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
    @author: Felipe Zago <felipe.zago@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/
odoo.define("l10n_br_pos_cfe.ReceiptScreen", function (require) {
    "use strict";

    const ReceiptScreen = require("point_of_sale.ReceiptScreen");
    const Registries = require("point_of_sale.Registries");
    const {useListener} = require("web.custom_hooks");
    const {useExternalListener} = owl.hooks;

    const L10nBrPosCfeReceiptScreen = (ReceiptScreen_) =>
        class extends ReceiptScreen_ {
            setup() {
                super.setup();

                useListener("autoprint", this.cfePrinting);
                useExternalListener(
                    window,
                    "footer-mounted",
                    this.triggerAutoPrintEvent
                );
            }

            // @override
            async handleAutoPrint() {
                return;
            }

            triggerAutoPrintEvent() {
                if (this._shouldAutoPrint()) {
                    this.trigger("autoprint");
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
