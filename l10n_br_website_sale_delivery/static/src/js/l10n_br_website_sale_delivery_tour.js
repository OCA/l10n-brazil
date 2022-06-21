odoo.define("l10n_br_website_sale_delivery.tour", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var session = require("web.session");
    var tour = require("web_tour.tour");

    var domReady = new Promise(function (resolve) {
        $(resolve);
    });
    var ready = Promise.all([domReady, session.is_bound, ajax.loadXML()]);

    tour.register(
        "l10n_br_website_sale_delivery_tour",
        {
            test: true,
            url: "/shop",
            wait_for: ready,
        },
        [
            {
                content: "search storage box",
                trigger: 'form input[name="search"]',
                run: "text storage box",
            },
            {
                content: "search storage box",
                trigger: 'form:has(input[name="search"]) .oe_search_button',
            },
            {
                content: "select storage box",
                trigger: '.oe_product_cart:first a:contains("Storage Box")',
                timeout: 10000,
            },
            {
                content: "click on add to cart",
                trigger:
                    '#product_detail form[action^="/shop/cart/update"]' +
                    " .btn-primary",
            },
            {
                content: "click in modal on 'Proceed to checkout' button",
                trigger: 'a:contains("Process Checkout")',
                run: function () {
                    window.location.href = "/shop/address";
                    // Redirect in JS to avoid the RPC loop (20x1sec)
                },
                timeout: 20000,
            },
            {
                content: "Complete name",
                trigger: "input[name='name']",
                run: "text Paradeda",
            },
            {
                content: "Complete phone",
                trigger: "input[name='phone']",
                run: "text 12981901669",
            },
            {
                content: "Complete zip",
                trigger: "input[name='zip']",
                run: "text 12246250",
            },
            {
                content: "check state is São Paulo",
                trigger: 'select[name=state_id]:contains("São Paulo")',
                run: function () {
                    setTimeout(function () {
                        console.log("wait for zip");
                    }, 8000);
                },
                timeout: 5000,
            },
            {
                content: "check city is São José dos Campos",
                trigger: 'select[name=city_id]:contains("São José dos Campos")',
                timeout: 5000,
            },
            {
                content: "Complete number",
                trigger: "input[name='street_number']",
                run: "text 23",
            },
            {
                content: "click in Next",
                trigger: 'a:contains("Next")',
                timeout: 20000,
            },
            {
                content:
                    "Free delivery charges - Make sure the price is loaded asynchronously",
                extra_trigger: '#delivery_carrier input[name="delivery_type"]:checked',
                trigger:
                    '#delivery_method .o_delivery_carrier_select:contains("Free delivery charges")',
                run: "click",
            },
            {
                content: "Check Free delivery chargese",
                extra_trigger:
                    '#delivery_carrier label:containsExact("Free delivery charges")',
                trigger: "#delivery_carrier span:contains('Free')",
            },
            {
                content: "The Test Poste - Ensure price was loaded asynchronously",
                extra_trigger: '#delivery_carrier input[name="delivery_type"]:checked',
                trigger:
                    '#delivery_method .o_delivery_carrier_select:contains("The Test Poste")',
                run: "click",
            },
            {
                content: "Check The Test Poste",
                extra_trigger:
                    '#delivery_carrier label:containsExact("The Test Poste")',
                trigger: "#delivery_carrier span:contains('20.0')",
            },

            {
                content: "Pay Now",
                // Either there are multiple payment methods, and one is checked, either there is only one, and therefore there are no radio inputs
                extra_trigger:
                    '#payment_method label:contains("Wire Transfer") input:checked,#payment_method:not(:has("input:radio:visible"))',
                trigger: 'button[id="o_payment_form_pay"]:visible:not(:disabled)',
            },
            {
                content: "finish",
                trigger: '.oe_website_sale:contains("Please make a payment to:")',
                // Leave /shop/confirmation to prevent RPC loop to
                //      /shop/payment/get_status.
                // The RPC could be handled in python while the tour is
                //      killed (and the session), leading to crashes
                run: function () {
                    // Redirect in JS to avoid the RPC loop (20x1sec)
                    window.location.href = "/aboutus";
                },
                timeout: 30000,
            },
        ]
    );
});
