odoo.define("l10n_br_website_sale.tour", function (require) {
    "use strict";

    var session = require("web.session");
    var tour = require("web_tour.tour");

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
                content: "click in modal on 'ADD TO CART' button",
                trigger: 'a:contains("ADD TO CART")',
            },
            {
                content: "click on add to cart",
                trigger: '#product_detail form[action^="/shop/cart"]' + " .btn-primary",
            },
            {
                content: "Go directly to /shop/checkout",
                trigger: "body",
                run: function () {
                    window.location.href = "/shop/checkout";
                },
                timeout: 10000,
            },
            {
                content: "Go directly to /shop/checkout",
                trigger: "body",
                run: function () {
                    window.location.href = "/shop/address";
                },
                timeout: 10000,
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
                content: "Complete mobile",
                trigger: "input[name='mobile']",
                run: "text 12981901669",
            },
            {
                content: "Complete CPF",
                trigger: "input[name='vat']",
                run: "text 89604455095",
            },
            {
                content: "Complete NUMBER",
                trigger: "input[name='street_number']",
                run: "text 200",
            },
            {
                content: "Complete DISTRICT",
                trigger: "input[name='district']",
                run: "text Cobre",
            },
            {
                content: "check state is São Paulo",
                trigger: 'select[name=state_id]:contains("São Paulo")',
                run: function () {
                    setTimeout(function () {
                        console.log("wait for zip");
                    }, 8000);
                },
                timeout: 20000,
            },
            {
                content: "check city is Adamantina",
                trigger: 'select[name=city_id]:contains("Adamantina")',
                run: function () {
                    /* Keep empty ... */
                },
            },
            {
                content: "click in Next",
                trigger: 'a:contains("Next")',
                timeout: 20000,
            },
            {
                content: "click in modal Pay Now",
                trigger: 'button[type="submit"]',
                timeout: 20000,
            },
        ]
    );
});
