// Copyright 2020 KMEE
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

/* global PagSeguro*/
/* eslint no-undef: "error"*/
odoo.define("payment_pagseguro.pagseguro_tokenize_card", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var PaymentForm = require("payment.payment_form");

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
            let button = ev.target;
            if (ev.type === "submit") {
                button = $(ev.target).find('*[type="submit"]')[0];
            }
            this.disableButton(button);
            if (this.options.partnerId === undefined) {
                console.warn(
                    "payment_form: unset partner_id when adding new token; things could go wrong"
                );
            }

            var acquirerID = this.getAcquirerIdFromRadio($checkedRadio);
            var acquirerForm = this.$("#o_payment_add_token_acq_" + acquirerID);
            var ds = $('input[name="data_set"]', acquirerForm)[0];
            var inputsForm = $("input", acquirerForm);
            var formData = this.getFormData(inputsForm);

            // Get public key
            rpc.query({
                route: "/payment/pagseguro/public_key",
                params: {acquirer_id: acquirerID},
            })
                .then(function (public_key) {
                    // Get encrypted card
                    return PagSeguro.encryptCard({
                        publicKey: public_key,
                        holder: formData.cc_holder_name,
                        number: formData.cc_number.replace(/\s+/g, ""),
                        expMonth: formData.cc_expiry.split("/")[0],
                        expYear: ""
                            .concat("20", formData.cc_expiry.split("/")[1])
                            .replace(/\s/g, ""),
                        securityCode: formData.cc_cvc,
                    });
                })
                .then(function (card) {
                    // Update card token
                    if (card.encryptedCard) {
                        return (formData.cc_token = card.encryptedCard);
                    }
                    // Wrong card info
                    self.enableButton(button);
                    self.displayError(
                        _t(card.errors[0].code),
                        _t(card.errors[0].message)
                    );
                })
                .then(function (result) {
                    if (result) {
                        // Remove credit card information for security purpose
                        _.extend(formData, {
                            cc_number: "",
                            cc_expiry: "",
                            cc_cvc: "",
                            data_set: ds.dataset.createRoute,
                        });
                        // Start payment flow
                        return rpc.query({
                            route: formData.data_set,
                            params: formData,
                        });
                    }
                })
                .then(function (result) {
                    if (result) {
                        $checkedRadio.val(result.id);
                        self.el.submit();
                    }
                })
                .catch(function (error) {
                    // If the public key rpc fails
                    self.enableButton(button);

                    if (error.data && error.data.message === "401: Unauthorized") {
                        self.displayError(
                            _t("Token inválido"),
                            _t("Por favor, comunique a loja sobre esse erro.")
                        );
                    } else {
                        self.displayError(
                            _t("Error info"),
                            _t(
                                "We are not able to add your payment method at the moment. "
                            )
                        );
                    }
                });
        },

        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------

        /**
         * @override
         *
         * This function is triggered when you click on the "pay now" button.
         */
        payEvent: function (ev) {
            ev.preventDefault();
            var $checkedRadio = this.$('input[type="radio"]:checked');

            // First we check that the user has selected a pagseguro as s2s payment method
            if (
                $checkedRadio.length === 1 &&
                $checkedRadio.data("provider") === "pagseguro" &&
                this.isNewPaymentRadio($checkedRadio)
            ) {
                return this._createPagseguroToken(ev, $checkedRadio);
            }
            return this._super.apply(this, arguments);
        },
    });
});
