import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as PaymentScreen from "@point_of_sale/../tests/tours/utils/payment_screen_util";
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import * as ReceiptScreen from "@point_of_sale/../tests/tours/utils/receipt_screen_util";
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("l10n_br_pos_nfce_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            ProductScreen.clickDisplayedProduct("Led Lamp"),
            ProductScreen.selectedOrderlineHas("Led Lamp", "1"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Dinheiro"),
            PaymentScreen.clickValidate(),
            ReceiptScreen.receiptIsThere(),
            {
                content: "the NFC-e receipt layout is rendered",
                trigger: ".pos-receipt .headerNfce",
            },
        ].flat(),
});
