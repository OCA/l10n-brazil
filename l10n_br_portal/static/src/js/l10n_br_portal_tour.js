odoo.define("l10n_br_portal.tour", function (require) {
    "use strict";

    var session = require("web.session");
    var tour = require("web_tour.tour");

    var domReady = new Promise(function (resolve) {
        $(resolve);
    });
    var ready = Promise.all([domReady, session.is_bound]);

    tour.register(
        "l10n_br_portal_tour",
        {
            url: "/my/account",
            test: true,
            wait_for: ready,
        },
        [
            {
                content: "Complete name",
                trigger: "input[name='name']",
                run: "text Mileo",
            },
            {
                content: "Complete CPF",
                trigger: "input[name='vat']",
                run: "text 89604455095",
            },
            {
                content: "Complete Company Name",
                trigger: "input[name='company_name']",
                run: "text Empresa X",
            },
            {
                content: "Complete State Tax Number",
                trigger: "input[name='l10n_br_ie_code']",
                run: "text ISENTO",
            },
            {
                content: "Complete Municipal Tax Number",
                trigger: "input[name='l10n_br_im_code']",
                run: "text 12345",
            },
            {
                content: "Complete ZIP",
                trigger: "input[name='zipcode']",
                run: "text 37500015",
            },
            {
                content: "Complete DISTRICT",
                trigger: "input[name='district']",
                run: "text Teste",
            },
            {
                content: "Complete NUMBER",
                trigger: "input[name='street_number']",
                run: "text 200",
            },
            {
                content: "check country is Brasil",
                trigger: 'select[name=country_id]:contains("Brazil")',
                run: function () {
                    /* Keep empty ... */
                },
            },
            {
                content: "check state is Minas Gerais",
                trigger: 'select[name=state_id]:contains("Minas Gerais")',
                run: function () {
                    /* Keep empty ... */
                },
            },
            {
                content: "check city is Itajubá",
                trigger: 'select[name=city_id]:contains("Itajubá")',
                run: function () {
                    /* Keep empty ... */
                },
            },
            {
                trigger: "button[type='submit']",
                run: "click",
            },
        ]
    );
});
