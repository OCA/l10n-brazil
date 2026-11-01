import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    async document_send() {
        if (this.document_type !== "65") {
            return super.document_send(...arguments);
        }

        if (!this.get_partner() && this.config.partner_id) {
            this.set_partner(this.config.partner_id);
        }

        // The NFC-e is issued by the backend while the order is invoiced.
        this.set_to_invoice(true);

        return true;
    },

    export_for_printing() {
        const result = super.export_for_printing(...arguments);

        if (this.config.simplified_document_type !== "65") {
            return result;
        }

        const company = this.company;

        result.company = Object.assign({}, result.company || {}, {
            cnpj_cpf: company.vat,
            inscr_est: company.l10n_br_ie_code,
            legal_name: company.legal_name,
            address: {
                street_name: company.street_name,
                street_number: company.street_number,
                district: company.district,
                city: company.city || "",
                zip: company.zip,
                state: company.state_id ? company.state_id.code : "",
            },
        });

        return {
            ...result,
            nfce_environment: this.config.nfce_environment,
            nfce_orderlines: this.getSortedOrderlines().map((line) => ({
                productName: line.get_full_product_name(),
                product_default_code: line.get_product().default_code || "",
                unit_code: line.product_id.uom_id ? line.product_id.uom_id.name : "",
                quantity: line.get_quantity(),
                unit_price: line.get_unit_display_price(),
                price_without_tax: line.get_price_without_tax(),
            })),
            is_nfce: true,
            ...this._buildNFCeAdditionalInfo(),
        };
    },

    _buildNFCeAdditionalInfo() {
        return {
            url_consulta: this.url_consulta,
            qr_code: this.qr_code,
            authorization_protocol: this.authorization_protocol,
            authorization_date_string: this.authorization_date_string,
            document_date_string: this.document_date_string,
            document_key: this.document_key,
            document_number: this.document_number,
            document_serie: this.document_serie,
        };
    },
});

patch(PosStore.prototype, {
    /**
     * After the backend authorizes the NFC-e, fetch its fiscal data.
     * @param {Array} orders Orders synchronized with the backend.
     */
    async postSyncAllOrders(orders) {
        await super.postSyncAllOrders(...arguments);

        if (this.config.simplified_document_type === "65") {
            await this._fillNFCeAdditionalInfo(orders);
        }
    },

    async _fillNFCeAdditionalInfo(orders) {
        const order = orders && orders[0];

        if (!order || !order.account_move) {
            return;
        }

        const accountMoveId = order.account_move.id || order.account_move;
        const [move] = await this.data.call("account.move", "read", [
            [accountMoveId],
            [
                "document_serie",
                "document_number",
                "document_key",
                "document_date",
                "authorization_date",
                "authorization_protocol",
                "fiscal_document_id",
            ],
        ]);

        if (!move) {
            return;
        }

        let supplement = null;

        if (move.fiscal_document_id) {
            const [document] = await this.data.call("l10n_br_fiscal.document", "read", [
                [move.fiscal_document_id[0]],
                ["nfe40_infNFeSupl"],
            ]);

            if (document && document.nfe40_infNFeSupl) {
                const [data] = await this.data.call(
                    "l10n_br_fiscal.document.supplement",
                    "read",
                    [[document.nfe40_infNFeSupl[0]], ["qrcode", "url_key"]]
                );
                supplement = data || null;
            }
        }

        Object.assign(order, {
            authorization_protocol: move.authorization_protocol,
            document_key: move.document_key,
            document_number: move.document_number,
            document_serie: move.document_serie,
            authorization_date_string: move.authorization_date,
            document_date_string: move.document_date,
            qr_code: supplement ? supplement.qrcode : false,
            url_consulta: supplement ? supplement.url_key : false,
        });
    },
});
