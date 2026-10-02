/* global Cleave */

import {CustomerAddress} from "@portal/interactions/address";
import {patch} from "@web/core/utils/patch";
import {patchDynamicContent} from "@web/public/utils";
import {rpc} from "@web/core/network/rpc";

patch(CustomerAddress.prototype, {
    setup() {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            "input[name='zip']": {"t-on-input": this.onChangeZip.bind(this)},
        });

        if (this.addressForm.vat) {
            this.cleaveVat = new Cleave(this.addressForm.vat, {
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
        if (this.addressForm.zip) {
            this.cleaveZip = new Cleave(this.addressForm.zip, {
                blocks: [5, 3],
                delimiter: "-",
                numericOnly: true,
            });
        }
    },

    async onChangeState() {
        await super.onChangeState(...arguments);
        this._filterCitiesByState();
    },

    _filterCitiesByState() {
        const citySelect = this.addressForm.city_id;
        if (!citySelect) return;

        const stateId = this.addressForm.state_id.value;
        let hasVisibleOption = false;
        for (const option of citySelect.options) {
            if (!option.value) continue;
            const visible = option.getAttribute("data-state_id") === stateId;
            option.hidden = !visible;
            hasVisibleOption = hasVisibleOption || visible;
            if (!visible && option.selected) {
                citySelect.value = "";
            }
        }
        this._setVisibility("#div_city_id", hasVisibleOption);
    },

    async onChangeZip() {
        const data = await rpc("/l10n_br/zip_search", {
            zipcode: this.addressForm.zip.value,
        });
        if (data.error) {
            return;
        }
        this.addressForm.district.value = data.district;
        this.addressForm.street_name.value = data.street_name;
        this.addressForm.country_id.value = data.country_id;
        // Repopulate the state <select> options for the new country (this is
        // normally done by the base class in reaction to a real "change"
        // event on the country <select>, which the line above doesn't
        // trigger). Calling the base implementation directly (instead of
        // `this._onChangeCountry`) avoids re-entering our own override.
        await super._onChangeCountry();
        this._updateBrazilianFieldsVisibility();
        this.addressForm.state_id.value = data.state_id;
        this._filterCitiesByState();
        this.addressForm.city_id.value = data.city_id;
    },

    _setVisibility(selector, shouldShow) {
        this.addressForm.querySelectorAll(selector).forEach((el) => {
            el.classList.toggle("d-none", !shouldShow);
            el.querySelectorAll("input, select").forEach(
                (field) => (field.disabled = !shouldShow)
            );
            if (el.tagName === "INPUT" || el.tagName === "SELECT") {
                el.disabled = !shouldShow;
            }
        });
    },

    _updateBrazilianFieldsVisibility() {
        const isBrazil = this._getSelectedCountryCode() === "BR";
        this._setVisibility(".o_standard_address", !isBrazil);
        this._setVisibility(".o_extended_address", isBrazil);
    },

    async _onChangeCountry() {
        await super._onChangeCountry(...arguments);
        this._updateBrazilianFieldsVisibility();
        if (this._getSelectedCountryCode() === "BR") {
            this.onChangeZip();
        }
    },
});
