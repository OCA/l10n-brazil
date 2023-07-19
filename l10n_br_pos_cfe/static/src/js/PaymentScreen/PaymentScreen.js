/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nBrPosCfePaymentScreen = (PaymentScreen_screen = PaymentScreen) =>
        class extends PaymentScreen_screen {
            async validateOrder(isForceValidate) {
                if (this.env.pos.config.iface_fiscal_via_proxy) {
                    super.validateOrder(isForceValidate);
                } else {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("No Tax Processor Configured"),
                        body: this.env._t(
                            "It was not possible to communicate with the tax processor. Please contact support."
                        ),
                    });
                }
            }
        };

    Registries.Component.extend(PaymentScreen, L10nBrPosCfePaymentScreen);

    return L10nBrPosCfePaymentScreen;
});
