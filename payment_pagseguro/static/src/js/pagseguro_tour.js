// Copyright 2020 KMEE
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define("payment_pagseguro.tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");
    var base = require("web_editor.base");
    var rpc = require("web.rpc");

    tour.register(
        "shop_buy_pagseguro",
        {
            url: "/shop",
            test: true,
            wait_for: base.ready(),
            debug: true,
        },
        [
            {
                content: "setup acquirer configurations",
                trigger: 'form input[name="search"]',
                run: function () {
                    var args = [[["provider", "=", "pagseguro"]]];
                    rpc.query({
                        model: "payment.acquirer",
                        method: "search",
                        args: args,
                    }).then(function (acquirer) {
                        return rpc.query({
                            model: "payment.acquirer",
                            method: "write",
                            args: [
                                acquirer,
                                {
                                    pagseguro_token: "8EC2714B10DC42DE882BC341A5366899",
                                    environment: "test",
                                    website_published: true,
                                    journal_id: 1,
                                    capture_manually: true,
                                    payment_flow: "s2s",
                                },
                            ],
                        });
                    });
                },
            },
            {
                content: "search conference chair",
                trigger: 'form input[name="search"]',
                run: "text conference chair",
            },
            {
                content: "search conference chair",
                trigger: 'form:has(input[name="search"]) .oe_search_button',
            },
            {
                content: "select conference chair",
                trigger: '.oe_product_cart:first a:contains("Conference Chair")',
            },
            {
                content: "select Conference Chair Steel",
                extra_trigger: "#product_detail",
                trigger: "label:contains(Steel) input",
            },
            {
                content: "click on add to cart",
                extra_trigger: "label:contains(Steel) input:propChecked",
                trigger:
                    '#product_detail form[action^="/shop/cart/update"] .btn-primary',
            },
            {
                content: "click in modal on 'Proceed to checkout' button",
                trigger: 'button:contains("Proceed to Checkout")',
            },
            {
                content: "go to checkout",
                trigger: 'a[href*="/shop/checkout"]',
            },
            {
                content: "select payment",
                trigger: '#payment_method label:contains("Pagseguro")',
            },
            {
                content: "insert card number",
                trigger: "input[name='cc_number']",
                run: "text 4111111111111111",
            },
            {
                content: "insert card name",
                trigger: "input[name='cc_holder_name']",
                run: "text VISA",
            },
            {
                content: "insert expiration date",
                trigger: "input[name='cc_expiry']",
                run: "text 12/2030",
            },
            {
                content: "insert security code",
                trigger: "input[name='cc_cvc']",
                run: "text 123",
            },
            {
                content: "pay now",
                // Either there are multiple payment methods, and one is checked, either there is only one, and therefore there are no radio inputs
                extra_trigger:
                    '#payment_method label:contains("Pagseguro") input:checked,#payment_method:not(:has("input:radio:visible"))',
                trigger: 'button[id="o_payment_form_pay"]:visible:not(:disabled)',
            },
            {
                content: "payment authorized",
                extra_trigger: ".bg-success",
                trigger:
                    '.bg-success span:contains("Your payment has been authorized.")',
                timeout: 20000,
            },
            {
                content: "finish",
                trigger: "body",
                // Leave /shop/confirmation to prevent RPC loop to
                //      /shop/payment/get_status.
                // The RPC could be handled in python while the tour is
                //      killed (and the session), leading to crashes
                run: function () {
                    // Redirect in JS to avoid the RPC loop (20x1sec)
                    window.location.href = "/aboutus";
                },
            },
        ]
    );
});
