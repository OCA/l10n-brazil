/** @odoo-module **/

import session from "web.session";
import tour from "web_tour.tour";

var domReady = new Promise(function (resolve) {
    $(resolve);
});
var ready = Promise.all([domReady, session.is_bound]);

tour.register(
    "l10n_br_website_sale_tour",
    {
        test: true,
        url: "/shop",
        wait_for: ready,
    },
    [
        {
            content: "search customizable desk",
            trigger: 'form input[name="search"]',
            run: "text customizable desk",
        },
        {
            content: "search customizable desk",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
        },
        {
            content: "select customizable desk",
            trigger: '.oe_product_cart:first a:contains("Customizable Desk")',
            timeout: 10000,
        },
        {
            content: "click on add to cart",
            trigger:
                '#product_detail form[action^="/shop/cart/update"]' +
                " .btn-primary",
        },
        {
            content: "click in modal on 'Proceed to Checkout' button",
            trigger: 'button:contains("Proceed to Checkout")',
            run: "click",
            timeout: 10000,
        },
        {
            content: "click on 'Process Checkout' button",
            trigger: 'a:contains("Process Checkout")',
            run: function () {
                window.location.href = "/shop/address";
                // Redirect in JS to avoid the RPC loop (20x1sec)
            },
            timeout: 10000,
        },
        {
            content: "Complete cpf",
            trigger: "input[name='cnpj_cpf']",
            run: "text 63639937090",
        },
        {
            content: "Complete zip",
            trigger: "input[name='zip']",
            run: "text 12246250",
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
            content: "check city is São José dos Campos",
            trigger: 'select[name=city_id]:contains("São José dos Campos")',
            timeout: 20000,
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
            content: "click in button Pay Now",
            trigger: 'button[type="submit"]',
            timeout: 20000,
        },
        {
            content: "finish",
            trigger: '.oe_website_sale_tx_status:contains("Your payment has been successfully processed. Thank you!")',
            // Leave /shop/confirmation to prevent RPC loop to
            //      /shop/payment/get_status.
            // The RPC could be handled in python while the tour is
            //      killed (and the session), leading to crashes
            run: function () {
                // Redirect in JS to avoid the RPC loop (20x1sec)
                window.location.href = "/aboutus";
            },
            timeout: 30000,
        }
    ]
);
