odoo.define("l10n_br_website_sale.l10n_br_address", function (require) {
    "use strict";

    const ajax = require("web.ajax");
    const publicWidget = require("web.public.widget");

    publicWidget.registry.L10nBrCheckoutAddress = publicWidget.Widget.extend({
        selector: ".checkout_autoformat[data-br-country]",
        events: {
            "change [name=country_id]": "_onCountryChange",
            "change [name=state_id]": "_onStateChange",
            "change [name=zip]": "_onZipChange",
            "input [name=company_name]": "_toggleTaxRegistrations",
        },

        start: function () {
            this.countryId = this.$("[name=country_id]").val();
            this._toggleAddressFields();
            return this._super.apply(this, arguments);
        },

        _isBrazil: function () {
            return this.$("[name=country_id]").val() === this.el.dataset.brCountry;
        },

        _toggleAddressFields: function () {
            const brazil = this._isBrazil();
            this.$(".o_br_address_field")
                .toggle(brazil)
                .find(":input")
                .prop("disabled", !brazil);
            this.$(".div_street, .div_city")
                .toggleClass("d-none", brazil)
                .find(":input")
                .prop("disabled", brazil);
            this.$(".o_br_vat_name").toggle(brazil);
            this.$(".o_regular_vat_name").toggle(!brazil);
            this.$(".div_vat, [name=company_name]")
                .closest(".col-lg-6")
                .toggle(brazil || this.el.dataset.b2b === "1");
            this._toggleTaxRegistrations();
        },

        _toggleTaxRegistrations: function () {
            const companyName = this.$("[name=company_name]").val() || "";
            const show = this._isBrazil() && Boolean(companyName.trim());
            this.$(".o_br_tax_registration")
                .toggle(show)
                .find(":input")
                .prop("disabled", !show);
        },

        _onCountryChange: function () {
            const countryId = this.$("[name=country_id]").val();
            // Odoo triggers this event on page load, including after validation errors.
            if (this.countryId !== undefined && this.countryId !== countryId) {
                this.$("[name=city_id] option:not(:first)").remove();
            }
            this.countryId = countryId;
            this._toggleAddressFields();
        },

        _onStateChange: function () {
            if (this._isBrazil()) {
                return this._loadCities();
            }
        },

        _loadCities: function (selectedCity) {
            const state = this.$("[name=state_id]").val();
            const city = this.$("[name=city_id]");
            city.find("option:not(:first)").remove();
            city.val("");
            if (!state) {
                return;
            }
            return ajax
                .jsonRpc("/shop/state_infos/" + state, "call", {})
                .then((data) => {
                    if (
                        !this._isBrazil() ||
                        this.$("[name=state_id]").val() !== state
                    ) {
                        return;
                    }
                    city.find("option:not(:first)").remove();
                    for (const [id, name] of data.cities) {
                        city.append(new Option(name, id, false, id === selectedCity));
                    }
                });
        },

        _onZipChange: function (event) {
            const zip = event.currentTarget.value.replace(/\D/g, "");
            if (!this._isBrazil() || zip.length !== 8) {
                return;
            }
            event.currentTarget.value = zip.slice(0, 5) + "-" + zip.slice(5);
            const formattedZip = event.currentTarget.value;
            return ajax
                .jsonRpc("/l10n_br/zip_search_public", "call", {zipcode: zip})
                .then((data) => {
                    if (
                        data.error ||
                        !this._isBrazil() ||
                        this.$("[name=zip]").val() !== formattedZip
                    ) {
                        return;
                    }
                    this.$("[name=district]").val(data.district);
                    this.$("[name=street_name]").val(data.street_name);
                    this.$("[name=state_id]").val(String(data.state_id));
                    return this._loadCities(data.city_id);
                });
        },
    });
});
