/* Copyright 2020 KMEE */
odoo.define("l10n_br_pox_pix", function(require) {
    "use strict";

    require("pos_qr_show");
    var rpc = require("web.rpc");
    var models = require("point_of_sale.models");

    models.load_fields("account.journal", ["pix_qr_type"]);

    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function() {
            var self = this;
            PosModelSuper.prototype.initialize.apply(this, arguments);
            this.bus.add_channel_callback("pix", this.on_pix, this);
        },
        on_pix: function(msg) {
            this.add_qr_payment(
                msg.order_ref,
                msg.journal_id,
                msg.total_fee,
                {},
                true
            );
        },
        pix_criar_cobranca: function(order, creg) {
            /* Send request asynchronously */
            var self = this;
            var pos = this;
            var terminal_ref = "POS/" + pos.config.name;
            var pos_id = pos.config.id;

            var lines = order.orderlines.map(function(r) {
                return {
                    // Always use 1 because quantity is taken into account in price field
                    quantity: 1,
                    quantity_full: r.get_quantity(),
                    price: r.get_price_with_tax(),
                    product_id: r.get_product().id,
                };
            });

            // Send without repeating on failure
            return rpc
                .query({
                    model: "l10n_br_pix.cob",
                    method: "create_pix_cobranca",
                    kwargs: {
                        lines: lines,
                        order_ref: order.uid,
                        pay_amount: order.get_due(),
                        terminal_ref: terminal_ref,
                        pos_id: pos_id,
                        journal_id: creg.journal.id,
                    },
                })
                .then(function(data) {
                    if (data.code_url) {
                        self.on_payment_qr(order, data.code_url);
                    } else if (data.error) {
                        self.show_warning(data.error);
                    } else {
                        self.show_warning("Unknown error");
                    }
                });
        },
    });

    var OrderSuper = models.Order;
    models.Order = models.Order.extend({
        add_paymentline: function(cashregister) {
            if (cashregister.journal.pix_qr_type === "payer") {
                this.pos.pix_criar_cobranca(this, cashregister);
                return;
            }
            return OrderSuper.prototype.add_paymentline.apply(this, arguments);
        },
    });

});
