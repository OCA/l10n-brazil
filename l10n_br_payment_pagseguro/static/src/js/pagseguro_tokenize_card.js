odoo.define('l10n_br_payment_pagseguro.pagseguro_tokenize_card', function (require){
    "use strict";

    var ajax = require('web.ajax');
    var PaymentForm = require('payment.payment_form');

    console.log("tokenize");

    var PagseguroPaymentForm = PaymentForm.include({

        willStart: function () {
            return this._super.apply(this, arguments).then(function () {
                // Get url min pagseguro
                return ajax.loadJS("");
            })
        },
    
        payEvent: function (ev) {
            ev.preventDefault();
            var $checkedRadio = this.$('input[type="radio"]:checked');
    
            // first we check that the user has selected a stripe as s2s payment method
            if ($checkedRadio.length === 1 && $checkedRadio.data('provider') === 'pagseguro' && this.isNewPaymentRadio($checkedRadio)) {
                var cvc =  $('#cc_cvc')[0].value;
                var expiry = $('#cc_expiry')[0].value;
                var holder_name = $('#cc_holder_name')[0].value;
                var number = $('#cc_number')[0].value;
                
                // Call function encrypt card

            }

            return this._super.apply(this, arguments);
        },

    });

});
