/* Copyright 2020 KMEE
   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */
/* global PagSeguro */
odoo.define("payment_pagseguro.payment_form", (require) => {
    "use strict";

    const core = require("web.core");
    const {loadJS} = require("@web/core/assets");

    const checkoutForm = require("payment.checkout_form");
    const manageForm = require("payment.manage_form");

    const _t = core._t;

    const SDK_URL =
        "https://assets.pagseguro.com.br/checkout-sdk-js/rc/dist/browser/pagseguro.min.js";

    const pagseguroMixin = {
        /**
         * Return the inline form inputs of the provider.
         *
         * @private
         * @param {Number} providerId - The id of the selected provider
         * @returns {Object} - The inline form inputs, keyed by their name
         */
        _getInlineFormInputs: function (providerId) {
            return {
                number: document.getElementById(`o_pagseguro_card_${providerId}`),
                holder: document.getElementById(`o_pagseguro_holder_${providerId}`),
                month: document.getElementById(`o_pagseguro_month_${providerId}`),
                year: document.getElementById(`o_pagseguro_year_${providerId}`),
                code: document.getElementById(`o_pagseguro_code_${providerId}`),
            };
        },

        /**
         * Load the SDK of PagBank and fetch the public key of the merchant.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {String} code - The code of the selected payment option's provider
         * @param {Number} paymentOptionId - The id of the selected payment option
         * @param {String} flow - The online payment flow of the selected payment option
         * @returns {Promise}
         */
        _prepareInlineForm: function (code, paymentOptionId, flow) {
            if (code !== "pagseguro") {
                return this._super(...arguments);
            }
            if (flow === "token") {
                // Tokens are handled by the generic flow.
                return Promise.resolve();
            }
            this._setPaymentFlow("direct");
            return loadJS(SDK_URL)
                .then(() => {
                    return this._rpc({
                        route: "/payment/pagseguro/public_key",
                        params: {provider_id: paymentOptionId},
                    });
                })
                .then((publicKey) => {
                    this.pagseguroPublicKey = publicKey;
                })
                .guardedCatch((error) => {
                    error.event.preventDefault();
                    this._displayError(
                        _t("Server Error"),
                        _t("An error occurred when displaying this payment form."),
                        error.message.data.message
                    );
                });
        },

        /**
         * Encrypt the card with the SDK and send the result to the server.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {String} code - The code of the selected payment option's provider
         * @param {Number} paymentOptionId - The id of the selected payment option
         * @param {String} flow - The online payment flow of the selected payment option
         * @returns {Promise}
         */
        _processPayment: function (code, paymentOptionId, flow) {
            if (code !== "pagseguro" || flow === "token") {
                // Tokens are handled by the generic flow.
                return this._super(...arguments);
            }

            if (!this._validateFormInputs(paymentOptionId)) {
                // The submit button is disabled and the page blocked at this point.
                this._enableButton();
                $("body").unblock();
                return Promise.resolve();
            }

            const inputs = this._getInlineFormInputs(paymentOptionId);
            const card = PagSeguro.encryptCard({
                publicKey: this.pagseguroPublicKey,
                holder: inputs.holder.value,
                number: inputs.number.value.replace(/ /g, ""),
                expMonth: inputs.month.value,
                expYear: inputs.year.value,
                securityCode: inputs.code.value,
            });
            if (!card.hasErrors) {
                return this._pagseguroPay(paymentOptionId, card, inputs.holder.value);
            }
            this._displayError(
                _t("Incorrect Payment Details"),
                _t("Please verify the card details and try again."),
                card.errors.map((error) => error.code).join(" ")
            );
            this._enableButton();
            $("body").unblock();
            return Promise.resolve();
        },

        /**
         * Create the transaction and send the encrypted card to the server.
         *
         * @private
         * @param {Number} providerId - The id of the selected provider
         * @param {Object} card - The card encrypted by the SDK
         * @param {String} cardHolder - The name of the card holder
         * @returns {Promise}
         */
        _pagseguroPay: function (providerId, card, cardHolder) {
            return this._rpc({
                route: this.txContext.transactionRoute,
                params: this._prepareTransactionRouteParams(
                    "pagseguro",
                    providerId,
                    "direct"
                ),
            })
                .then((processingValues) => {
                    return this._rpc({
                        route: "/payment/pagseguro/payment",
                        params: {
                            reference: processingValues.reference,
                            partner_id: processingValues.partner_id,
                            access_token: processingValues.access_token,
                            encrypted_card: card.encryptedCard,
                            card_holder: cardHolder,
                        },
                    }).then(() => (window.location = "/payment/status"));
                })
                .guardedCatch((error) => {
                    error.event.preventDefault();
                    this._displayError(
                        _t("Server Error"),
                        _t("We are not able to process your payment."),
                        error.message.data.message
                    );
                });
        },

        /**
         * Check that all the inline form inputs adhere to the DOM constraints.
         *
         * @private
         * @param {Number} providerId - The id of the selected provider
         * @returns {Boolean} - Whether all the inputs pass the validation constraints
         */
        _validateFormInputs: function (providerId) {
            const inputs = Object.values(this._getInlineFormInputs(providerId));
            return inputs.every((element) => element.reportValidity());
        },
    };

    checkoutForm.include(pagseguroMixin);
    manageForm.include(pagseguroMixin);
});
