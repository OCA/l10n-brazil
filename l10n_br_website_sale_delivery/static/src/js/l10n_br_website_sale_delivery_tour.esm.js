/** @odoo-module **/

import * as tourUtils from "@website_sale/js/tours/tour_utils";
import {registry} from "@web/core/registry";

const carrierSelector = "#o_delivery_methods [name='o_delivery_method']";
const paidCarrier = "Freight Test Poste";
const freeCarrier = "Freight Test Free";

function fill(name, value) {
    return {trigger: 'input[name="' + name + '"]:visible', run: "fill " + value};
}

function carrierInput(name) {
    return carrierSelector + ":has(label:text(" + name + ")) input";
}

function selectCarrier(name) {
    return {trigger: carrierInput(name) + ":enabled", run: "click"};
}

function checkAmounts(name, delivery, total) {
    return {
        content: "Check the selected carrier and the order totals",
        trigger:
            'body:has(a[name="website_sale_main_button"]:not(.disabled):not([disabled])) ' +
            carrierInput(name) +
            ":checked:enabled",
        run: () => {
            const shownDelivery = document
                .querySelector("#order_delivery .monetary_field")
                ?.textContent.trim();
            const shownTotal = document
                .querySelector("#order_total .monetary_field")
                ?.textContent.trim();
            if (!shownDelivery?.endsWith(delivery) || !shownTotal?.endsWith(total)) {
                throw new Error(
                    "Unexpected delivery " + shownDelivery + " or total " + shownTotal
                );
            }
        },
    };
}

registry.category("web_tour.tours").add("l10n_br_website_sale_delivery_tour", {
    steps: () => [
        {trigger: "#add_to_cart", run: "click"},
        tourUtils.goToCart({quantity: 1}),
        tourUtils.goToCheckout(),
        fill("name", "Freight Checkout Customer"),
        fill("email", "freight-checkout@example.com"),
        fill("phone", "12981901669"),
        fill("zip", "12246250"),
        fill("street_number", "23"),
        {
            trigger: 'select[name="city_id"]:has(option:nth-child(2))',
            run: () => {
                const city = document.querySelector('select[name="city_id"]');
                if (
                    city.selectedOptions[0]?.textContent.trim() !==
                    "São José dos Campos"
                ) {
                    throw new Error(
                        "The CEP lookup did not select São José dos Campos"
                    );
                }
            },
        },
        fill("vat", "89604455095"),
        {trigger: "#save_address", run: "click", expectUnloadPage: true},
        selectCarrier(freeCarrier),
        checkAmounts(freeCarrier, "0.00", "100.00"),
        selectCarrier(paidCarrier),
        checkAmounts(paidCarrier, "20.00", "120.00"),
        {
            trigger: "#o_delivery_methods",
            run: () => {
                window.location.href = "/shop/cart";
            },
            expectUnloadPage: true,
        },
        {trigger: 'a[aria-label="Add one"]', run: "click"},
        {
            content: "Check the cart quantity and the updated total",
            trigger: ".my_cart_quantity:text(2)",
            run: () => {
                const total = document
                    .querySelector("#order_total .monetary_field")
                    ?.textContent.trim();
                if (!total?.endsWith("220.00")) {
                    throw new Error("Expected cart total 220.00, got " + total);
                }
            },
        },
        tourUtils.goToCheckout(),
        checkAmounts(paidCarrier, "20.00", "220.00"),
        {
            trigger: "#o_delivery_methods",
            run: () => window.location.reload(),
            expectUnloadPage: true,
        },
        checkAmounts(paidCarrier, "20.00", "220.00"),
        tourUtils.confirmOrder(),
        {trigger: "#address_on_payment"},
    ],
});
