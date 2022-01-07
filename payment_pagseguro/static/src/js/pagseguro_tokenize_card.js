/* global PagSeguro*/
/* eslint no-undef: "error"*/
odoo.define("payment_pagseguro.pagseguro_tokenize_card", function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PaymentForm = require('payment.payment_form');

    var _t = core._t;

    PaymentForm.include({
        willStart: function () {
            return this._super.apply(this, arguments).then(function () {
                // Get url min pagseguro
                return ajax.loadJS(
                    "https://assets.pagseguro.com.br/checkout-sdk-js/rc/dist/browser/pagseguro.min.js"
                );
            });
        },

        _createPagseguroToken: function (ev, $checkedRadio) {
            var self = this;
            if (ev.type === 'submit') {
                var button = $(ev.target).find('*[type="submit"]')[0]
            } else {
                var button = ev.target;
            }
            this.disableButton(button);

            if (this.options.partnerId === undefined) {
                console.warn('payment_form: unset partner_id when adding new token; things could go wrong');
            }
                var acquirerID = this.getAcquirerIdFromRadio($checkedRadio, );
                var acquirerForm = this.$('#o_payment_add_token_acq_' + acquirerID);
                var ds = $('input[name="data_set"]', acquirerForm)[0];
                var inputsForm = $('input', acquirerForm);
                var formData = this.getFormData(inputsForm);

                // Get public key
                rpc.query({
                    route: "/payment/pagseguro/public_key",
                    params: {acquirer_id: acquirerID},
                }).then(function (data) {
                    // Call function encrypt card
                   return PagSeguro.encryptCard({
                        publicKey: data,
                        holder: formData.cc_holder_name,
                        number: formData.cc_number.replace(/\s+/g, ""),
                        expMonth: formData.cc_expiry.split("/")[0],
                        expYear: formData.cc_expiry.split("/")[1],
                        securityCode: formData.cc_cvc,
                    });
                }).then(function (card) {
                    // Update card token and call parent function
                    if (card.encryptedCard){
                        return formData.cc_token = card.encryptedCard;
                    } else {
                        return $.Deferred().reject({"message": {"data": { "message": card.error.message}}});
                    }
                }).then(function(result) {
                    if (result.error) {
                        return $.Deferred().reject({"message": {"data": { "message": result.error.message}}});
                    } else {
                        _.extend(formData, {"data_set": ds.dataset.createRoute});
                    
                        return rpc.query({
                            route: formData.data_set,
                            params: formData,
                        })
                    }
                }).then(function(result) {
                    $checkedRadio.val(result.id);
                    self.el.submit();
                }).fail(function (error, event) {
                    // if the rpc fails, pretty obvious
                    self.enableButton(button);
                    self.displayError(
                        _t('Unable to save card'),
                        _t("We are not able to add your payment method at the moment. ")
                    );
                });
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @override
         * 
         * This function is triggered when you click on the "pay now" button.
         */
        payEvent: function (ev) {
            ev.preventDefault();
            var $checkedRadio = this.$('input[type="radio"]:checked');

            // first we check that the user has selected a pagseguro as s2s payment method
            if ($checkedRadio.length === 1 && $checkedRadio.data('provider') === 'pagseguro' && this.isNewPaymentRadio($checkedRadio)) {
                return this._createPagseguroToken(ev, $checkedRadio);
            } else {
                return this._super.apply(this, arguments);
            }
        },

    });
});
