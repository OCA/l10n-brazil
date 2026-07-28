/* Copyright 2023 KMEE
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
odoo.define("payment_bacen_pix.payment_status", (require) => {
    "use strict";

    const publicWidget = require("web.public.widget");

    const POLL_INTERVAL = 5000;

    publicWidget.registry.BacenPixStatus = publicWidget.Widget.extend({
        selector: "#o_bacenpix_status",

        /**
         * Poll the state of the transaction until it leaves the pending states.
         *
         * @override
         * @returns {Promise}
         */
        start: function () {
            this.reference = this.el.dataset.reference;
            this.accessToken = this.el.dataset.accessToken;
            this.timeout = setInterval(this._poll.bind(this), POLL_INTERVAL);
            return this._super(...arguments);
        },

        /**
         * @override
         */
        destroy: function () {
            clearInterval(this.timeout);
            this._super(...arguments);
        },

        /**
         * Ask the server for the state of the transaction.
         *
         * @private
         * @returns {Promise}
         */
        _poll: function () {
            return this._rpc({
                route: "/payment/bacenpix/status",
                params: {
                    reference: this.reference,
                    access_token: this.accessToken,
                },
            }).then((result) => {
                if (result.state !== "draft" && result.state !== "pending") {
                    clearInterval(this.timeout);
                    window.location = "/payment/status";
                }
            });
        },
    });

    return publicWidget.registry.BacenPixStatus;
});
