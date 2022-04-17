/*
    l10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_br_tef.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');

    screens.PaymentScreenWidget.include({

        render_paymentlines: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.$('.paymentlines-container').unbind('click').on('click', '.tef-payment-terminal-transaction-start', function (event) {
                // Why this "on" thing links severaltime the button to the action
                // if I don't use "unlink" to reset the button links before ?
                // self.pos.get_order().tef_in_transaction = true;
                // self.order_changes();
                self.pos.tef_client.start_operation('purchase', self);
            });
        },

        order_changes: function () {
            this._super.apply(this, arguments);
            var order = this.pos.get_order();
            if (!order) {
                return;
            } else if (order.tef_in_transaction) {
                this.$('.tef_in_transaction').removeClass('oe_hidden');
            } else {
                this.$('.tef_in_transaction').addClass('oe_hidden');
            }
        }
    });

});
