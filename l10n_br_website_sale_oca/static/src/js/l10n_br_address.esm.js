/** @odoo-module **/

import {rpc} from "@web/core/network/rpc";
import WebsiteSaleAddress from "@website_sale/js/address";

WebsiteSaleAddress.include({
    events: {
        ...WebsiteSaleAddress.prototype.events,
        "input input[name='zip']": "_onBrZip",
        "input input[name='company_name']": "_toggleBrTaxRegistrations",
    },

    _isBrAddress() {
        return (
            this.addressForm.dataset.brCompany === "1" &&
            this.addressForm.country_id.selectedOptions[0]?.getAttribute("code") ===
                "BR"
        );
    },

    async _changeCountry() {
        await this._super(...arguments);
        if (this.addressForm.dataset.brCompany !== "1") {
            return;
        }
        const br = this._isBrAddress();
        const form = this.addressForm;
        for (const input of form.querySelectorAll(
            ".o_br_address_field :is(input, select)"
        )) {
            input.disabled = !br;
            input.parentElement.style.display = br ? "" : "none";
        }
        for (const field of ["street", "city"]) {
            form[field].disabled = br;
            if (br) {
                this._hideInput(field);
            }
        }
        const b2b = form.dataset.brB2b === "1";
        for (const id of ["#company_name_div", "#div_vat"]) {
            const container = form.querySelector(id);
            if (container) {
                container.style.display = br || b2b ? "" : "none";
                container.querySelector("input").disabled = !(br || b2b);
            }
        }
        const labels = form.querySelectorAll(".o_br_vat_label, .o_regular_vat_label");
        for (const label of labels) {
            label.style.display =
                label.classList.contains("o_br_vat_label") === br ? "" : "none";
        }
        this._toggleBrTaxRegistrations();
        if (br) {
            await this._loadBrCities();
        }
    },

    async _onChangeState() {
        await this._super(...arguments);
        if (this._isBrAddress()) {
            await this._loadBrCities();
        }
    },

    async _loadBrCities(selectedCity) {
        const state = this.addressForm.state_id.value;
        const city = this.addressForm.city_id;
        if (!state) {
            city.options.length = 1;
            return;
        }
        const result = await rpc("/shop/state_infos/" + state, {});
        if (!this._isBrAddress() || state !== this.addressForm.state_id.value) {
            return;
        }
        const cityId = selectedCity === undefined ? city.value : selectedCity;
        city.options.length = 1;
        for (const [id, name] of result.cities) {
            city.add(new Option(name, id, false, Number(cityId) === id));
        }
    },

    _toggleBrTaxRegistrations() {
        const form = this.addressForm;
        const visible = this._isBrAddress() && Boolean(form.company_name?.value.trim());
        for (const input of form.querySelectorAll(".o_br_tax_registration input")) {
            input.disabled = !visible;
            input.parentElement.style.display = visible ? "" : "none";
        }
    },

    async _onBrZip() {
        const form = this.addressForm;
        const code = form.zip.value.replace(/\D/g, "");
        if (!this._isBrAddress() || code.length !== 8) {
            return;
        }
        const result = await rpc("/l10n_br/zip_search_public", {
            zipcode: code,
            csrf_token: form.csrf_token.value,
        });
        if (
            result.error ||
            !this._isBrAddress() ||
            code !== form.zip.value.replace(/\D/g, "")
        ) {
            return;
        }
        form.zip.value = code.slice(0, 5) + "-" + code.slice(5);
        form.street_name.value = result.street_name || "";
        form.district.value = result.district || "";
        form.state_id.value = result.state_id;
        await this._loadBrCities(result.city_id);
    },
});
