odoo.define('l10n_br_portal.tour', function (require) {
    'use strict';

    var tour = require('web_tour.tour');
    var base = require("web_editor.base");

    tour.register('l10n_br_portal_tour', {
        test: true,
        url: '/my/account',
        wait_for: base.ready()
    }, [{
        content: "Complete name",
        trigger: "input[name=name]",
        run: "text Luis Felipe Mileo2",
    }, {
        content: "Complete Legal Name",
        trigger: "input[name=legal_name]",
        run: "text Luis Felipe Mileo LTDA2",
    }, {
        content: "Complete CNPJ",
        trigger: "input[name=cnpj_cpf]",
        run: "text 89604455095",
    }, {
        content: "Complete IE",
        trigger: "input[name=inscr_est]",
        run: "text ISENTO",
    }, {
        content: "Complete INVALID Zip",
        trigger: "input[name=zipcode]",
        run: "text 00000000",
    }, {
        content: "Complete ZIP",
        trigger: "input[name=zipcode]",
        run: "text 37500015",
    }, {
        content: "check city is Itajubá",
        trigger: 'select[name=city_id]:contains("Itajubá")',
        run: function () { /* keep empty ... */},
    }, {
        content: "Submit Portal",
        trigger: 'button[type=submit]',
    }]);
});
