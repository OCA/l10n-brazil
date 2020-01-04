odoo.define('l10n_br_portal.tour', function (require) {
    'use strict';

    var tour = require('web_tour.tour');

    tour.register('l10n_br_portal_tour', {
        test: true,
        url: '/my/account',
    }, [{
        content: "Complete name",
        trigger: "input[name=name]",
        run: "text KMEE",
    }, {
        content: "Complete Legal Name",
        trigger: "input[name=legal_name]",
        run: "text KMEE INFORMATICA LTDA",
    }, {
        content: "Complete CNPJ",
        trigger: "input[name=cnpj_cpf]",
        run: "text 23130935000198",
    }, {
        content: "Complete IE",
        trigger: "input[name=inscr_est]",
        run: "text ISENTO",
    }, {
        content: "Complete ZIP",
        trigger: "input[name=zipcode]",
        run: "text 37500-015",
    }, {
        content: "check city is Itajubá",
        trigger: 'select[name=city_id]:contains("Itajubá")',
        run: function () { /* keep empty ... */},
    }, {
        content: "Submit Portal",
        trigger: 'button[type=submit]',
    }]);
});
