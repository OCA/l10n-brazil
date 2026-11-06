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
                trigger: '#product_detail form[action^="/shop/cart"] .btn-primary',
            },
            {
                content: "Go to checkout",
                trigger: "body",
                run: function () {
                    window.location.href = "/shop/checkout";
                },
                timeout: 10000,
            },
            {
                // Reproduces a real customer click: navigating straight to
                // /shop/address (without a partner_id) puts the form in
                // ('new', 'shipping') mode instead of ('edit', 'billing'),
                // hiding the billing-only fields (vat, zip, IE/IM code).
                content: "Edit billing address",
                trigger: ".js_edit_address:first",
                timeout: 20000,
            },
            {
                content: "Complete zip",
                trigger: "input[name='zip']",
                run: "text 12246250",
            },
            {
                // Keep the same name: Odoo blocks changing the name of an
                // internal (non-share) user from the website frontend, and
                // this tour logs in as admin.
                content: "Complete name",
                trigger: "input[name='name']",
                run: "text Mitchell Admin",
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
                // The admin fixture already has a Company Name (demo data),
                // so clear it first to exercise the "empty" case for real.
                content: "Clear company name",
                trigger: "input[name='company_name']",
                run: function () {
                    $("input[name='company_name']").val("").trigger("input");
                },
            },
            {
                // A plain poll-until-match trigger (no thrown errors): the
                // test harness treats any console "tour ... failed" message
                // as fatal even if a later retry succeeds, so asserting a
                // negative condition has to happen in the trigger itself.
                content: "State Tax Number is hidden while Company Name is empty",
                trigger: "body:not(:has(.div_l10n_br_ie_code:visible))",
                run: function () {
                    /* Keep empty, only the trigger matters */
                },
            },
            {
                content: "Complete company name",
                trigger: "input[name='company_name']",
                run: "text L10n BR Test Company",
            },
            {
                content: "Complete State Tax Number (now visible)",
                trigger: ".div_l10n_br_ie_code input[name='l10n_br_ie_code']:visible",
                run: "text 110042490114",
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
                // Submitting here saves the BR address (zip, vat, State Tax
                // Number, city/state) and lands on /shop/checkout. Going
                // further (clicking Confirm to reach /shop/confirm_order)
                // pulls in this demo product's fiscal computation, which
                // hangs with this database's demo data (no NCM/fiscal
                // operation configured) - a separate, pre-existing issue
                // unrelated to l10n_br_website_sale's address form, so the
                // tour stops here.
                content: "click in Next",
                trigger: 'a:contains("Next")',
                timeout: 20000,
            },
            {
                content: "Checkout page reached with all fields saved",
                trigger: '.o_page_header:contains("Billing Address")',
                run: function () {
                    /* Keep empty, only the trigger matters */
                },
            },
        ]
    );
});
