/** @odoo-module **/
// Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
// License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

/* eslint-disable sort-imports */

import {onWillStart} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {ListRenderer} from "@web/views/list/list_renderer";
import {ViewButton} from "@web/views/view_button/view_button";

patch(ViewButton.prototype, "l10n_br_fiscal.ViewButton", {
    onClick() {
        if (this.props.className && this.props.className.includes("edit-line-popup")) {
            if (this.props.record) {
                this.env.bus.trigger("OPEN_LINE_IN_POPUP", {
                    record: this.props.record,
                });
            }
            return;
        }
        this._super.apply(this, arguments);
    },
});

patch(ListRenderer.prototype, "l10n_br_fiscal.ListRenderer", {
    setup() {
        this._super.apply(this, arguments);

        onWillStart(() => {
            this.env.bus.on("OPEN_LINE_IN_POPUP", this, ({record}) => {
                if (this.props.list.records.includes(record)) {
                    this.props.openRecord(record);
                }
            });
        });
    },
});
