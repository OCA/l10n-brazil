/** @odoo-module **/
/* global Cleave, console */

import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.l10nBrPortalDetails = publicWidget.Widget.extend({
    selector: ".o_portal_details",
    events: {
        "change select[name='state_id']": "_onChangeState",
        "change input[name='zipcode']": "_onChangeZipcode",
    },

    start: function () {
        if (this.$(".input-vat").length) {
            this.cleaveVat = new Cleave(this.$(".input-vat")[0], {
                blocks: [2, 3, 3, 4, 2],
                delimiters: [".", ".", "-"],
                numericOnly: true,
                onValueChanged: function (e) {
                    if (e.target.rawValue.length > 11) {
                        this.properties.blocks = [2, 3, 3, 4, 2];
                        this.properties.delimiters = [".", ".", "/", "-"];
                    } else {
                        this.properties.blocks = [3, 3, 3, 3];
                        this.properties.delimiters = [".", ".", "-"];
                    }
                },
            });
        }

        if (this.$(".input-zipcode").length) {
            this.cleaveZipcode = new Cleave(this.$(".input-zipcode")[0], {
                blocks: [5, 3],
                delimiter: "-",
                numericOnly: true,
            });
        }

        this.stateOptions = this.$("select[name='city_id']:enabled option:not(:first)");
        this.$("select[name='state_id']").change();

        return this._super.apply(this, arguments);
    },

    _onChangeState: function (e) {
        if (!this.stateOptions) {
            return;
        }
        var select = this.$("select[name='city_id']");
        this.stateOptions.detach();
        var displayedState = this.stateOptions.filter(
            "[data-state_id=" + ($(e.currentTarget).val() || 0) + "]"
        );
        var nb = displayedState.appendTo(select).show().length;
        select.parent().toggle(nb >= 1);
    },

    _onChangeZipcode: function () {
        var vals = {zipcode: this.$('input[name="zipcode"]').val()};
        console.log("Changing ZIP");

        rpc("/l10n_br/zip_search", vals).then((data) => {
            if (data.error) {
                console.log("Falha ao consultar cep");
            } else {
                this.$('input[name="district"]').val(data.district);
                this.$('input[name="street_name"]').val(data.street_name);
                this.$('select[name="country_id"]').val(data.country_id).change();
                this.$('select[name="state_id"]').val(data.state_id).change();
                this.$('select[name="city_id"]').val(data.city_id);
            }
        });
    },
});
