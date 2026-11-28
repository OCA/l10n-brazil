/** @odoo-module **/

import * as tourUtils from "@website_sale/js/tours/tour_utils";
import {registry} from "@web/core/registry";

function fill(name, value) {
    return {trigger: 'input[name="' + name + '"]:visible', run: "fill " + value};
}

function checkCity() {
    return {
        trigger: 'select[name="city_id"]:has(option:nth-child(2))',
        run: () => {
            const city = document.querySelector('select[name="city_id"]');
            if (city.selectedOptions[0]?.textContent.trim() !== "Adamantina") {
                throw new Error("The CEP lookup did not select Adamantina");
            }
        },
    };
}

function addToCart(email) {
    return [
        {trigger: "#add_to_cart", run: "click"},
        tourUtils.goToCart({quantity: 1}),
        tourUtils.goToCheckout(),
        fill("name", "Checkout Customer"),
        fill("email", email),
        fill("phone", "12981901669"),
    ];
}

const submit = {trigger: "#save_address", run: "click", expectUnloadPage: true};

registry.category("web_tour.tours").add("l10n_br_website_sale_oca_tour", {
    steps: () => [
        ...addToCart("checkout-br@example.com"),
        {trigger: 'input[name="street_name"]:visible'},
        fill("zip", "12246250"),
        fill("street_number", "200"),
        checkCity(),
        fill("vat", "123"),
        {trigger: "#save_address", run: "click"},
        {trigger: 'input[name="vat"].is-invalid', run: "edit 89604455095"},
        checkCity(),
        {
            content: "Tax registrations are hidden for a person",
            trigger: ".checkout_autoformat:not(:has(.o_br_tax_registration:visible))",
        },
        fill("company_name", "Checkout Test Company"),
        fill("l10n_br_ie_code", "110042490114"),
        submit,
        {trigger: "#address_on_payment"},
    ],
});

registry.category("web_tour.tours").add("l10n_br_website_sale_oca_foreign_tour", {
    steps: () => [
        ...addToCart("checkout-fr@example.com"),
        {trigger: 'select[name="country_id"]', run: "selectByLabel France"},
        fill("street", "1 rue de la Paix"),
        fill("city", "Paris"),
        fill("zip", "75000"),
        {
            ...submit,
            trigger: 'form:has(select[name="state_id"]:not(:required)) #save_address',
        },
        {trigger: "#address_on_payment"},
    ],
});
