/*
    L10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_br_tef.widgets", function (require) {
    "use strict";

    const chrome = require("point_of_sale.chrome");
    const gui = require("point_of_sale.gui");
    const PopupWidget = require("point_of_sale.popups");
    const widgets = chrome.Chrome.prototype.widgets;

    const TefStatusWidget = chrome.StatusWidget.extend({
        template: "TefStatusWidget",

        set_tef_status: function (status) {
            if (status.state === "connected") {
                const warning = false;
                const msg = "";
                this.set_status(warning ? "warning" : "connected", msg);
            } else {
                this.set_status(status.state, "");
            }
        },

        start: function () {
            this.set_tef_status(this.pos.get("tef_status"));
            this.pos.bind("change:tef_status", (pos, tef_status) => {
                this.set_status(tef_status.state, tef_status.pending);
            });

            // Forces reconnection to the TEF client
            this.$el.click(() => {
                this.pos.tef_client.connect();
            });

            // TODO: Lidar com o cancelamento/estorno;
            // let cancel_btn = $('.btn-cancelar-pagamento');
            // cancel_btn.hide();
            //
            // if (this.pos.config.iface_tef) {
            //     cancel_btn.show();
            //     cancel_btn.unbind('click').on("click", function (event) {
            //         self.pos_widget.payment_screen.cancel_payment()
            //     });
            // }
        },
    });

    widgets.splice(_.indexOf(_.pluck(widgets, "name"), "notification"), 0, {
        name: "l10n_br_tef_status_widget",
        widget: TefStatusWidget,
        append: ".pos-rightheader",
        condition: function () {
            return this.pos.config.iface_tef;
        },
    });

    // FIXME: Adapt the popup to the new pos structure
    const CancelamentoCompraPopup = PopupWidget.extend({
        template: "PurchaseCancellationWidget",

        show: function (options) {
            const self = this;
            this._super(options);

            $(".btn-report_data").unbind("click");
            // TODO: Check if this bind makes sense. At first the search_handler is only used for product search.
            this.el
                .querySelector(".btn-report_data")
                .addEventListener("click", this.search_handler);
            $(".btn-report_data", this.el).click(function () {
                self.pos_widget.product_screen.proceed_cancellation();
            });

            $(".btn-cancel-operation").unbind("click");
            // TODO: Check if this bind makes sense. At first the search_handler is only used for product search.
            this.el
                .querySelector(".btn-cancel-operation")
                .addEventListener("click", this.search_handler);
            $(".btn-cancel-operation", this.el).click(function () {
                self.pos_widget.product_screen.abort();
            });
        },
    });

    // FIXME: Adapt the popup to the new pos structure
    const ConfirmaCancelamentoCompraPopup = PopupWidget.extend({
        template: "PurchaseCancellationConfirmWidget",

        show: function (options) {
            const self = this;
            this._super();

            this.message = options.message || "";
            this.comment = options.comment || "";
            this.renderElement();

            $(".btn-confirm-cancellation").unbind("click");
            // TODO: Check if this bind makes sense. At first the search_handler is only used for product search.
            this.el
                .querySelector(".btn-confirm-cancellation")
                .addEventListener("click", this.search_handler);
            $(".btn-confirm-cancellation", this.el).click(function () {
                self.pos_widget.product_screen.confirm_proceed_cancellation(true);
            });

            $(".btn-cancel-cancellation").unbind("click");
            // TODO: Check if this bind makes sense. At first the search_handler is only used for product search.
            this.el
                .querySelector(".btn-cancel-cancellation")
                .addEventListener("click", this.search_handler);
            $(".btn-cancel-cancellation", this.el).click(function () {
                self.pos_widget.product_screen.confirm_proceed_cancellation(false);
            });
        },
    });

    const StatusPagementoPopUp = PopupWidget.extend({
        template: "PaymentStatusWidget",

        show: function (options) {
            this._super();
            this.message = options.title || "";
            this.comment = options.body || "";
            this.renderElement();
        },
    });

    gui.define_popup({
        name: "CancelamentoCompraPopup",
        widget: CancelamentoCompraPopup,
    });
    gui.define_popup({
        name: "ConfirmaCancelamentoCompraPopup",
        widget: ConfirmaCancelamentoCompraPopup,
    });
    gui.define_popup({name: "StatusPagementoPopUp", widget: StatusPagementoPopUp});

    return {
        TefStatusWidget: TefStatusWidget,
        CancelamentoCompraPopup: CancelamentoCompraPopup,
        ConfirmaCancelamentoCompraPopup: ConfirmaCancelamentoCompraPopup,
        StatusPagementoPopUp: StatusPagementoPopUp,
    };
});
