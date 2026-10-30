/* Copyright 2020 KMEE INFORMATICA LTDA
   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */
odoo.define("payment_cielo.payment_form", (require) => {
    "use strict";

    const core = require("web.core");

    const checkoutForm = require("payment.checkout_form");
    const manageForm = require("payment.manage_form");

    const _t = core._t;

    const cieloMixin = {
        /**
         * Return the inline form inputs of the provider.
         *
         * @private
         * @param {Number} providerId - The id of the selected provider
         * @returns {Object} - The inline form inputs, keyed by their name
         */
        _getInlineFormInputs: function (providerId) {
            return {
                number: document.getElementById(`o_cielo_card_${providerId}`),
                holder: document.getElementById(`o_cielo_holder_${providerId}`),
                month: document.getElementById(`o_cielo_month_${providerId}`),
                year: document.getElementById(`o_cielo_year_${providerId}`),
                code: document.getElementById(`o_cielo_code_${providerId}`),
            };
        },

        /**
         * Return the card details to send to the server.
         *
         * @private
         * @param {Number} providerId - The id of the selected provider
         * @returns {Object} - The card details
         */
        _getPaymentDetails: function (providerId) {
            const inputs = this._getInlineFormInputs(providerId);
            return {
                card_number: inputs.number.value.replace(/ /g, ""),
                card_holder: inputs.holder.value,
                card_expiry: `${inputs.month.value}/${inputs.year.value}`,
                card_verification_code: inputs.code.value,
            };
        },

        /**
         * Prepare the inline form of Cielo for direct payment.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {String} code - The code of the selected payment option's provider
         * @param {Number} paymentOptionId - The id of the selected payment option
         * @param {String} flow - The online payment flow of the selected payment option
         * @returns {Promise}
         */
        _prepareInlineForm: function (code, paymentOptionId, flow) {
            if (code !== "cielo") {
                return this._super(...arguments);
            }
            if (flow === "token") {
                // Tokens are handled by the generic flow.
                return Promise.resolve();
            }
            this._setPaymentFlow("direct");
            return Promise.resolve();
        },

        /**
         * Send the card details to the server, which forwards them to Cielo.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {String} code - The code of the selected payment option's provider
         * @param {Number} paymentOptionId - The id of the selected payment option
         * @param {String} flow - The online payment flow of the selected payment option
         * @returns {Promise}
         */
        _processPayment: function (code, paymentOptionId, flow) {
            if (code !== "cielo" || flow === "token") {
                // Tokens are handled by the generic flow.
                return this._super(...arguments);
            }

            if (!this._validateFormInputs(paymentOptionId)) {
                // The submit button is disabled and the page blocked at this point.
                this._enableButton();
                $("body").unblock();
                return Promise.resolve();
            }

            const cardData = this._getPaymentDetails(paymentOptionId);
            return this._rpc({
                route: this.txContext.transactionRoute,
                params: this._prepareTransactionRouteParams(
                    "cielo",
                    paymentOptionId,
                    "direct"
                ),
            })
                .then((processingValues) => {
                    return this._rpc({
                        route: "/payment/cielo/payment",
                        params: {
                            reference: processingValues.reference,
                            partner_id: processingValues.partner_id,
                            access_token: processingValues.access_token,
                            card_data: cardData,
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

    checkoutForm.include(cieloMixin);
    manageForm.include(cieloMixin);
});
