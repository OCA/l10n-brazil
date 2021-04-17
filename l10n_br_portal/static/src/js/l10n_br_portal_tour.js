odoo.define('l10n_br_portal.tour', function (require) {
    'use strict';

    var tour = require('web_tour.tour');
    var base = require("web_editor.base");

    tour.register('l10n_br_portal_tour', {
        url: '/my/account',
        test: true,
        wait_for: base.ready(),
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
            run: function () { /* keep empty ... */},
        },
        {
            trigger: "button[type='submit']",
        },
        {
            trigger: ".o_portal_my_home",
        },
    ]);
});
