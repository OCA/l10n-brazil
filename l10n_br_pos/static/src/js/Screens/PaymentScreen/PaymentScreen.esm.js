/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
@author: Gabriel Cardoso <gabriel.cardoso@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {validate_cnpj_cpf} from "@l10n_br_pos/js/util.esm";

patch(PaymentScreen.prototype, {
    check_valid_cpf_cnpj(order) {
        let result = true;
        const partner = order.get_partner();

        if (partner) {
            const cnpj_cpf = partner.vat || partner.name;

            result = validate_cnpj_cpf(cnpj_cpf);
            if (!result) {
                order.set_partner(null);
            }
        }

        return result;
    },

    /**
     * @override
     */
    async _isOrderValid() {
        const result = await super._isOrderValid(...arguments);

        if (!result) {
            return false;
        }

        if (this.pos.config.simplified_document_type) {
            const order = this.currentOrder;
            const isValid = this.check_valid_cpf_cnpj(order);

            if (isValid) {
                return await order.document_send(this);
            }
            this.dialog.add(AlertDialog, {
                title: _t("CNPJ / CPF Inválido !"),
                body: _t("Insira um número de CNPJ / CPF válido para o cliente."),
            });
            return false;
        }

        return result;
    },
});
