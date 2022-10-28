odoo.define("l10n_br_portal.tour", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var session = require("web.session");
    var tour = require("web_tour.tour");

    var domReady = new Promise(function (resolve) {
        $(resolve);
    });
    var ready = Promise.all([domReady, session.is_bound, ajax.loadXML()]);

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
                content: "Complete Legal Name",
                trigger: "input[name='legal_name']",
                run: "text Luis Felipe Mileo",
            },
            {
                content: "Complete CPF",
                trigger: "input[name='cnpj_cpf']",
                run: "text 89604455095",
            },
            {
                content: "Complete IE",
                trigger: "input[name='inscr_est']",
                run: "text ISENTO",
            },
            {
                content: "Complete ZIP",
                trigger: "input[name='zipcode']",
                run: "text 37500015",
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
            },
            {
                content: "Go /my url",
                trigger: 'a[href*="/my"]',
            },
        ]
    );
});
