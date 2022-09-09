/*
    L10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_br_tef.PaymentDestaxa", function (require) {
    "use strict";

    var PaymentInterface = require("point_of_sale.PaymentInterface");

    var DestaxaPaymentTerminal = PaymentInterface.extend({
        init: function () {
            this._super.apply(this, arguments);
            this.enable_reversals();
        },
        send_payment_request: function (cid) {
            this._super.apply(this, arguments);
            return this._destaxa_payment_terminal_pay(cid);
        },
        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            return this._destaxa_payment_terminal_cancel(order, cid);
        },
        send_payment_reversal: function (cid) {
            this._super.apply(this, arguments);
            return this._destaxa_payment_terminal_reversal(cid);
        },
        close: function () {
            this._super.apply(this, arguments);
            return this._destaxa_payment_terminal_close();
        },
        _destaxa_payment_terminal_pay: function (cid) {
            console.log("Destaxa Pay");
        },
        _destaxa_payment_terminal_cancel: function (order, cid) {
            console.log("Destaxa Cancel");
        },
        _destaxa_payment_terminal_reversal: function (cid) {
            console.log("Destaxa Reversal");
        },
        _destaxa_payment_terminal_close: function () {
            console.log("Destaxa Close");
        },
    });
    return DestaxaPaymentTerminal;
});
