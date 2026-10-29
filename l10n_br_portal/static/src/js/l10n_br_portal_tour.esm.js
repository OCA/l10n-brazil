import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("l10n_br_portal_tour", {
    url: "/my/account",
    test: true,
    steps: () => [
        {
            content: "Complete CPF",
            trigger: "input[name='vat']",
            run: function () {
                // Set value directly so Cleave processes the full string at once,
                // avoiding digit reordering that occurs with char-by-char keyboard events.
                this.anchor.value = "89604455095";
                $(this.anchor).trigger("input").trigger("change");
            },
        },
        {
            content: "Complete Company Name",
            trigger: "input[name='company_name']",
            run: "edit Empresa X",
        },
        {
            content: "Complete State Tax Number",
            trigger: "input[name='l10n_br_ie_code']",
            run: "edit ISENTO",
        },
        {
            content: "Complete Municipal Tax Number",
            trigger: "input[name='l10n_br_im_code']",
            run: "edit 12345",
        },
        {
            content: "Complete ZIP",
            trigger: "input[name='zip']",
            run: "edit 37500015",
        },
        {
            content: "Complete DISTRICT",
            trigger: "input[name='district']",
            run: "edit Teste",
        },
        {
            content: "Complete NUMBER",
            trigger: "input[name='street_number']",
            run: "edit 200",
        },
        {
            content: "check country is Brasil",
            trigger: "select[name='country_id']:has(option:checked:contains('Brazil'))",
        },
        {
            content: "check state is Minas Gerais",
            trigger:
                "select[name='state_id']:has(option:checked:contains('Minas Gerais'))",
        },
        {
            content: "check city is Itajubá",
            trigger: "select[name='city_id']:has(option:checked:contains('Itajubá'))",
        },
        {
            trigger: "#save_address",
            run: "click",
        },
    ],
});
