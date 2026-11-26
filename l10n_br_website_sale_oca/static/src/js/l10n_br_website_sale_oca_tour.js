odoo.define("l10n_br_website_sale_oca.tour", function (require) {
    "use strict";

    const tour = require("web_tour.tour");
    const tourUtils = require("website_sale.tour_utils");

    const addToCart = [
        {trigger: "#add_to_cart"},
        tourUtils.goToCart(),
        {trigger: 'a[href="/shop/checkout?express=1"]'},
    ];
    const next = {trigger: ".checkout_autoformat .a-submit"};
    const payment = {
        trigger: "#shipping_and_billing",
        run: () => {
            if (window.location.pathname !== "/shop/payment") {
                throw new Error("Checkout did not reach the payment page");
            }
        },
    };

    function fill(name, value) {
        return {trigger: `input[name="${name}"]:visible`, run: "text " + value};
    }

    function fillContact(email) {
        return [
            fill("name", "Checkout Customer"),
            fill("email", email),
            fill("phone", "12981901669"),
        ];
    }

    tour.register("l10n_br_website_sale_oca_tour", {test: true}, [
        ...addToCart,
        ...fillContact("checkout-br@example.com"),
        fill("zip", "12246250"),
        {
            trigger: 'input[name="street_number"]',
            run: "text 200",
        },
        {
            content: "Wait for the CEP lookup to fill the street and select the city",
            trigger:
                'select[name="city_id"]:has(option:selected:contains("Adamantina"))',
            run: () => null,
        },
        fill("vat", "123"),
        next,
        {trigger: 'input[name="vat"].is-invalid', run: "text 89604455095"},
        {
            content: "The selected city is retained when correcting the CPF",
            trigger:
                'select[name="city_id"]:has(option:selected:contains("Adamantina"))',
            run: () => null,
        },
        {
            content: "Tax registrations are hidden for a person",
            trigger: ".checkout_autoformat:not(:has(.o_br_tax_registration:visible))",
            run: () => null,
        },
        fill("company_name", "Checkout Test Company"),
        fill("l10n_br_ie_code", "110042490114"),
        next,
        payment,
    ]);

    tour.register("l10n_br_website_sale_oca_foreign_tour", {test: true}, [
        ...addToCart,
        ...fillContact("checkout-fr@example.com"),
        {
            trigger: 'select[name="country_id"]',
            run: function () {
                const countryId = window.sessionStorage.getItem(
                    "l10n_br_checkout_country"
                );
                window.sessionStorage.removeItem("l10n_br_checkout_country");
                $('select[name="country_id"]').val(countryId).trigger("change");
            },
        },
        fill("street", "1 rue de la Paix"),
        fill("city", "Paris"),
        fill("zip", "75000"),
        next,
        payment,
    ]);
});
