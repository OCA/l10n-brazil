/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos.PaymentScreen", function (require) {
    "use strict";

    const core = require("web.core");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const util = require("l10n_br_pos.util");
    const {Gui} = require("point_of_sale.Gui");
    const _t = core._t;

    const L10nBrPosPaymentScreen = (PaymentScreen_screen = PaymentScreen) =>
        class extends PaymentScreen_screen {
            check_valid_cpf_cnpj(order) {
                let result = true;
                const client = order.get_client();

                if (client) {
                    let cnpj_cpf = null;
                    if (client.cnpj_cpf) {
                        cnpj_cpf = client.cnpj_cpf;
                    } else {
                        cnpj_cpf = client.name;
                    }

                    result = util.validate_cnpj_cpf(cnpj_cpf);
                    if (!result) {
                        order.set_client(null);
                    }
                }

                return result;
            }

            async _isOrderValid(isForceValidate) {
                var result = super._isOrderValid(isForceValidate);
                if (this.env.pos.config.simplified_document_type) {
                    var order = this.env.pos.get_order();
                    const valid_cpf_cnpj = this.check_valid_cpf_cnpj(order);
                    if (valid_cpf_cnpj) {
                        result = await order.document_send(this);
                    } else {
                        Gui.showPopup("ErrorPopup", {
                            title: _t("Invalid CNPJ / CPF !"),
                            body: _t("Enter a valid CNPJ / CPF number"),
                        });
                    }
                }

                return result;
            }
        };

    Registries.Component.extend(PaymentScreen, L10nBrPosPaymentScreen);

    return L10nBrPosPaymentScreen;
});
