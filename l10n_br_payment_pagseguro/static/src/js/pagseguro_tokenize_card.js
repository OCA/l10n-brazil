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
                
                // RPC call to get public gey
                var public_key = this._rpc({
                    model: 'payment.acquirer',
                    method: '_get_pagseguro_environment'
                });

                console.log(public_key);
                
                // Call function encrypt card
                var card = PagSeguro.encryptCard({
                    publicKey: 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr+ZqgD892U9/HXsa7XqBZUayPquAfh9xx4iwUbTSUAvTlmiXFQNTp0Bvt/5vK2FhMj39qSv1zi2OuBjvW38q1E374nzx6NNBL5JosV0+SDINTlCG0cmigHuBOyWzYmjgca+mtQu4WczCaApNaSuVqgb8u7Bd9GCOL4YJotvV5+81frlSwQXralhwRzGhj/A57CGPgGKiuPT+AOGmykIGEZsSD9RKkyoKIoc0OS8CPIzdBOtTQCIwrLn2FxI83Clcg55W8gkFSOS6rWNbG5qFZWMll6yl02HtunalHmUlRUL66YeGXdMDC2PuRcmZbGO5a/2tbVppW6mfSWG3NPRpgwIDAQAB',
                    holder: holder_name,
                    number: number.replace(/\s+/g, ''),
                    expMonth: expiry.split("/")[0],
                    expYear: expiry.split("/")[1],
                    securityCode: cvc
                });

                var card_token = $('input[name="cc_token"]')[0];
                card_token.value = card.encryptedCard;
            }

            return this._super.apply(this, arguments);
        },

    });

});
