/** @odoo-module **/

import * as PaymentScreen from "@point_of_sale/../tests/tours/helpers/PaymentScreenTourMethods";
import * as ProductScreen from "@point_of_sale/../tests/tours/helpers/ProductScreenTourMethods";
import * as ReceiptScreen from "@point_of_sale/../tests/tours/helpers/ReceiptScreenTourMethods";
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("l10n_br_pos_tour", {
    test: true,
    url: "/pos/ui",
    steps: () =>
        [
            ProductScreen.clickDisplayedProduct("Desk Pad"),
            ProductScreen.selectedOrderlineHas("Desk Pad", "1"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Dinheiro"),
            PaymentScreen.clickValidate(),
            ReceiptScreen.receiptIsThere(),
        ].flat(),
});
