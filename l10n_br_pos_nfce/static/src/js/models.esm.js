/** @odoo-module **/

import {BRAZILIAN_STATES_IBGE_CODE_MAP, NFeXML} from "@l10n_br_pos_nfce/js/nfe-xml.esm";
import {Order, Orderline} from "@point_of_sale/app/store/models";
import {ChaveEdoc} from "@l10n_br_pos_nfce/js/utils.esm";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

const getFirst = (val) => (Array.isArray(val) ? val[0] : val);

patch(Order.prototype, {
    async document_send() {
        if (this.document_type !== "65") {
            return super.document_send(...arguments);
        }

        if (!this.get_partner()) {
            const anonymousPartner = this.pos.db.get_partner_by_id(
                getFirst(this.pos.config.partner_id) || false
            );

            if (anonymousPartner) {
                this.set_partner(anonymousPartner);
            }
        }

        // The NFC-e is issued by the backend while the order is invoiced.
        this.set_to_invoice(true);

        return true;
    },

    export_for_printing() {
        const result = super.export_for_printing(...arguments);

        if (this.pos.config.simplified_document_type !== "65") {
            return result;
        }

        const {
            cnpj_cpf,
            inscr_est,
            legal_name,
            street_name,
            street_number,
            district,
            city_id,
            zip,
            state_id,
        } = this.pos.company;

        const {nfce_environment} = this.pos.config;

        const companyInfo = {
            cnpj_cpf,
            inscr_est,
            legal_name,
            address: {
                street_name,
                street_number,
                district,
                city: city_id ? city_id[1] : "",
                zip,
                state: state_id ? state_id[1] : "",
            },
        };

        result.company = Object.assign({}, result.company || {}, companyInfo);

        result.nfce_environment = nfce_environment;

        return {
            ...result,
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

    _getFiscalMap(line) {
        const maps = this.pos.fiscal_map_by_template_id;
        return maps ? maps[getFirst(line.product.product_tmpl_id)] : false;
    },

    get_total_icms() {
        let totalICMS = 0;

        for (const line of this.get_orderlines()) {
            const productFiscalMap = this._getFiscalMap(line);

            if (productFiscalMap && productFiscalMap.icms_cst_code === "00") {
                totalICMS += parseFloat(productFiscalMap.icms_value) || 0;
            }
        }

        return totalICMS;
    },

    get_total_pis() {
        let totalPIS = 0;

        for (const line of this.get_orderlines()) {
            const productFiscalMap = this._getFiscalMap(line);

            if (productFiscalMap) {
                totalPIS += parseFloat(productFiscalMap.pis_value) || 0;
            }
        }

        return totalPIS;
    },

    get_total_cofins() {
        let totalCofins = 0;

        for (const line of this.get_orderlines()) {
            const productFiscalMap = this._getFiscalMap(line);

            if (productFiscalMap) {
                totalCofins += parseFloat(productFiscalMap.cofins_value) || 0;
            }
        }

        return totalCofins;
    },

    get_total_without_discount() {
        let totalWithoutDiscount = 0;

        for (const line of this.get_orderlines()) {
            totalWithoutDiscount +=
                (parseFloat(line.product.lst_price) || 0) *
                (parseFloat(line.quantity) || 0);
        }

        return totalWithoutDiscount;
    },

    get_total_icms_base() {
        let totalICMSBase = 0;

        for (const line of this.get_orderlines()) {
            const productFiscalMap = this._getFiscalMap(line);

            if (productFiscalMap && productFiscalMap.icms_cst_code === "00") {
                totalICMSBase += parseFloat(productFiscalMap.icms_base) || 0;
            }
        }

        return totalICMSBase;
    },
});

patch(Orderline.prototype, {
    getDisplayData() {
        const data = super.getDisplayData(...arguments);

        if (this.pos.config.simplified_document_type !== "65") {
            return data;
        }

        return {
            ...data,
            product_default_code: this.get_product().default_code || "",
            unit_code: this.get_unit().name || "",
            quantity: this.get_quantity(),
            unit_price: this.get_unit_display_price(),
            price_without_tax: this.get_price_without_tax(),
        };
    },
});

patch(PosStore.prototype, {
    /**
     * Keep the NFC-e flow on top of the standard order synchronization:
     * after the backend authorizes the document, fetch its fiscal data and,
     * if the backend is unreachable, fall back to contingency.
     * @param {Array} orders Orders to synchronize.
     * @returns {Promise<Array>} Backend ids of the synchronized orders.
     */
    async _save_to_server(orders) {
        if (this.config.simplified_document_type !== "65") {
            return super._save_to_server(...arguments);
        }

        let serverIds = [];
        try {
            serverIds = await super._save_to_server(...arguments);
        } catch (error) {
            if (error.code === 200) {
                throw error;
            }

            // Could not reach the backend: issue in contingency.
            this._contingenciaNFCe(orders);

            return orders.map((order) => ({
                pos_reference: order.data.name,
            }));
        }

        await this._fillNFCeAdditionalInfo(serverIds);

        return serverIds;
    },

    /**
     * Receive the authorized NFC-e data from the backend.
     * @param {Array} orders Result of create_from_ui.
     */
    async _fillNFCeAdditionalInfo(orders) {
        if (!orders || !orders.length) {
            return;
        }

        const currentOrder = this.get_order();

        if (!currentOrder) {
            return;
        }

        const orderOption = orders[0];

        if (!orderOption.account_move) {
            console.warn("NFC-e: create_from_ui did not return account_move.");
            return;
        }

        const moves = await this.orm.read(
            "account.move",
            [orderOption.account_move],
            [
                "document_serie",
                "document_number",
                "document_key",
                "document_date",
                "authorization_date",
                "authorization_protocol",
                "document_type",
                "fiscal_document_id",
            ]
        );

        if (!moves || !moves.length) {
            console.warn("NFC-e: account.move not found:", orderOption.account_move);
            return;
        }

        const move = moves[0];
        let supplement = null;

        if (move.fiscal_document_id) {
            const fiscalDocuments = await this.orm.read(
                "l10n_br_fiscal.document",
                [move.fiscal_document_id[0]],
                ["nfe40_infNFeSupl"]
            );

            if (fiscalDocuments.length && fiscalDocuments[0].nfe40_infNFeSupl) {
                const supplementId = fiscalDocuments[0].nfe40_infNFeSupl[0];

                const supplements = await this.orm.read(
                    "l10n_br_fiscal.document.supplement",
                    [supplementId],
                    ["qrcode", "url_key"]
                );

                if (supplements && supplements.length) {
                    supplement = supplements[0];
                }
            }
        }

        Object.assign(currentOrder, {
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

    /**
     * Contingency.
     *
     * The document number must come from the backend: the browser does not
     * touch the backend sequence, so no local number is invented here.
     * @param {Array} orders Orders that could not be synchronized.
     */
    _contingenciaNFCe(orders) {
        const state = this.company.state_id ? this.company.state_id[1] : "";

        const cnpj = (this.company.cnpj_cpf || "").replace(/\D/g, "");

        const currentDate = new Date();

        const yearMonth =
            currentDate.getFullYear().toString().slice(-2) +
            (currentDate.getMonth() + 1).toString().padStart(2, "0");

        const serie = this.config.nfce_document_serie_code
            ? this.config.nfce_document_serie_code.toString().padStart(3, "0")
            : "001";

        for (let i = 0; i < orders.length; i++) {
            const currentOrder = this.get_order();

            if (!currentOrder) {
                continue;
            }

            if (!currentOrder.document_number) {
                console.warn(
                    "NFC-e in contingency: document number not available yet."
                );
                continue;
            }

            currentOrder.document_serie = serie;

            const chaveEdoc = new ChaveEdoc(
                false,
                BRAZILIAN_STATES_IBGE_CODE_MAP[state],
                yearMonth,
                cnpj,
                this.config.simplified_document_type,
                serie,
                currentOrder.document_number.toString().padStart(9, "0"),
                "9"
            );

            currentOrder.document_key = chaveEdoc.generatedChave;

            currentOrder.document_date_string = currentDate.toLocaleString();

            this._qrCodeNFCeContingency(currentOrder, chaveEdoc);
        }
    },

    async _qrCodeNFCeContingency(currentOrder, chaveEdoc) {
        const xml = new NFeXML(this, currentOrder, chaveEdoc);

        currentOrder.qr_code = await xml.generateQRCodeText();
    },
});
