/*
    L10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_br_tef.screens", function (require) {
    "use strict";

    const screens = require("point_of_sale.screens");
    const core = require("web.core");
    const _t = core._t;

    screens.PaymentScreenWidget.include({
        render_paymentlines: function () {
            /*
             * Button bind to start a new TEF transaction
             */
            this._super.apply(this, arguments);
            this.$(".paymentlines-container")
                .unbind("click")
                .on("click", ".tef-payment-terminal-transaction-start", () => {
                    this.pos.get_order().tef_in_transaction = true;
                    this.order_changes();
                    this.pos.tef_client.start_operation("purchase", this);
                });
        },

        order_changes: function () {
            /*
             * Handles the loading icon for ongoing TEF transactions on
             *   the payment screen
             */
            this._super.apply(this, arguments);
            var order = this.pos.get_order();
            if (!order) {
                return;
            } else if (order.tef_in_transaction) {
                this.$(".tef_in_transaction").removeClass("oe_hidden");
            } else {
                this.$(".tef_in_transaction").addClass("oe_hidden");
            }
        },

        finalize_validation: function () {
            /*
             * Block payment completion if there are pending payments via TEF
             */
            const payment_lines = this.pos.get_order().get_paymentlines();
            const has_unpaid_lines = payment_lines.reduce((acc, line) => {
                if (!line.tef_payment_completed) {
                    acc = true;
                }
                return acc;
            }, false);

            if (has_unpaid_lines) {
                this.pos.gui.show_popup("alert", {
                    title: _t("Unpaid TEF transactions"),
                    body: _t("There are unpaid TEF transactions"),
                });
            } else {
                this._super.apply(this, arguments);
            }
        },

        get_selected_paymentline: function () {
            const order = this.pos.get_order();
            let paymentline = null;
            order.get_paymentlines().forEach(function (payment) {
                if (payment.selected) {
                    paymentline = payment;
                }
            });
            return paymentline;
        },
    });
});
