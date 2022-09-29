odoo.define("l10n_br_pos_cfe.SatOrderReceipt", function (require) {
    "use strict";

    const OrderReceipt = require("point_of_sale.OrderReceipt");

    /*
     * Overwrite the original component template, as it is giving OWL
     * error when we try to inherit and change the information from
     * the entire original template.
     */
    OrderReceipt.template = "SatOrderReceipt";

    return OrderReceipt;
});
