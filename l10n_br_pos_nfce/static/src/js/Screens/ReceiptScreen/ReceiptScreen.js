/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Ygor de Carvalho Andrade <ygor.carvalho@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_nfce.ReceiptScreen", function (require) {
    "use strict";

    const ReceiptScreen = require("point_of_sale.ReceiptScreen");
    const Registries = require("point_of_sale.Registries");
    const {useRef} = owl.hooks;

    const L10nBrPosNfceReceiptScreen = (_ReceiptScreen) =>
        class extends _ReceiptScreen {
            constructor() {
                super(...arguments);
                if (this.currentOrder.document_type === "65") {
                    this.orderReceipt = useRef("nfce-order-receipt");
                } else {
                    this.orderReceipt = useRef("order-receipt");
                }
            }
        };

    Registries.Component.extend(ReceiptScreen, L10nBrPosNfceReceiptScreen);

    return L10nBrPosNfceReceiptScreen;
});
