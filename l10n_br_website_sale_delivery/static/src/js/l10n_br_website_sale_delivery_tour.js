odoo.define("l10n_br_website_sale_delivery.tour", function (require) {
    "use strict";

    const tour = require("web_tour.tour");
    const tourUtils = require("website_sale.tour_utils");
    const carrierSelector = "#delivery_method .o_delivery_carrier_select";
    const checkout = {trigger: 'a[href="/shop/checkout?express=1"]'};

    function fill(name, value) {
        return {trigger: 'input[name="' + name + '"]:visible', run: "text " + value};
    }

    function selectCarrier(name) {
        return {
            trigger:
                carrierSelector + ':has(label:containsExact("' + name + '")) input',
        };
    }

    function checkAmounts(name, delivery, total) {
        return {
            trigger:
                carrierSelector +
                ':has(label:containsExact("' +
                name +
                '")) input:checked',
            extra_trigger:
                '#order_delivery .oe_currency_value:containsExact("' + delivery + '")',
            run: () => {
                const displayedTotal = $("#order_total .oe_currency_value")
                    .text()
                    .trim();
                if (displayedTotal !== total) {
                    throw new Error(
                        "Expected checkout total " + total + ", got " + displayedTotal
                    );
                }
            },
        };
    }

    tour.register("l10n_br_website_sale_delivery_tour", {test: true}, [
        {trigger: "#add_to_cart"},
        tourUtils.goToCart(),
        checkout,
        fill("name", "Freight Checkout Customer"),
        fill("email", "freight-checkout@example.com"),
        fill("phone", "12981901669"),
        fill("zip", "12246250"),
        fill("street_number", "23"),
        {
            trigger:
                'select[name="city_id"]:has(option:selected:contains("São José dos Campos"))',
            run: () => null,
        },
        fill("vat", "89604455095"),
        {trigger: ".checkout_autoformat .a-submit"},
        selectCarrier("Freight Test Free"),
        checkAmounts("Freight Test Free", "0.00", "100.00"),
        selectCarrier("Freight Test Poste"),
        checkAmounts("Freight Test Poste", "20.00", "120.00"),
        {
            trigger: "#delivery_method",
            run: () => {
                window.location.href = "/shop/cart";
            },
        },
        {trigger: 'input.js_quantity[value="1"] ~ a[aria-label="Add one"]'},
        {
            content: "Check the cart total after increasing the quantity",
            trigger: '.my_cart_quantity:containsExact("2")',
            run: () => {
                const displayed = $(".js_cart_summary").text().replace(/\s+/g, " ");
                if (
                    !displayed.includes("Delivery: R$ 20.00") ||
                    !displayed.includes("Total: R$ 220.00")
                ) {
                    throw new Error("Unexpected cart summary: " + displayed);
                }
            },
        },
        checkout,
        selectCarrier("Freight Test Poste"),
        checkAmounts("Freight Test Poste", "20.00", "220.00"),
        {
            trigger: "#delivery_method",
            run: () => {
                document.body.dataset.freightBeforeReload = "true";
                window.location.reload();
            },
        },
        {
            ...checkAmounts("Freight Test Poste", "20.00", "220.00"),
            content: "Confirm the freight and total after reloading checkout",
            trigger:
                "body:not([data-freight-before-reload]) " +
                carrierSelector +
                ':has(label:containsExact("Freight Test Poste")) input:checked',
        },
    ]);
});
