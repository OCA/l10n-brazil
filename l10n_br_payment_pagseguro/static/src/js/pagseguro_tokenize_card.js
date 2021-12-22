odoo.define('l10n_br_payment_pagseguro.pagseguro_tokenize_card', function (require){
    "use strict";

    var ajax = require('web.ajax');
    var PaymentForm = require('payment.payment_form');
    var rpc = require('web.rpc');

    var PagseguroPaymentForm = PaymentForm.include({

        willStart: function () {
            return this._super.apply(this, arguments).then(function () {
                // Get url min pagseguro
                return ajax.loadJS("https://assets.pagseguro.com.br/checkout-sdk-js/rc/dist/browser/pagseguro.min.js");
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
                var public_key = '';

                // Get public key
                rpc.query({
                    route: '/payment/pagseguro/public_key',
                    params: {'acquirer_id': $("input[name='acquirer_id']").val()}
                }).then(function(data){
                     // Call function encrypt card
                    var card = PagSeguro.encryptCard({
                        publicKey: data,
                        holder: holder_name,
                        number: number.replace(/\s+/g, ''),
                        expMonth: expiry.split("/")[0],
                        expYear: expiry.split("/")[1],
                        securityCode: cvc
                    });

                    var card_token = $('input[name="cc_token"]')[0];
                    card_token.value = card.encryptedCard;
                });
            }

            return this._super.apply(this, arguments);
        },

    });

});
