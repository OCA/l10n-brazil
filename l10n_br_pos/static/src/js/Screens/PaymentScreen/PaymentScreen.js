/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/


odoo.define("l10n_br_pos.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async _isOrderValid(isForceValidate) {
                var result = super._isOrderValid(isForceValidate);
                var order = this.env.pos.get_order();
                result = await order.document_send();
                return result;
            }
        };

    Registries.Component.extend(PaymentScreen, L10nBrPosPaymentScreen);

    return L10nBrPosPaymentScreen;
});
