/** @odoo-module **/

import {Order, PosGlobalState} from "point_of_sale.models";
import Registries from "point_of_sale.Registries";

import {ChaveEdoc} from "@l10n_br_pos_nfce/js/utils.esm";
import {BRAZILIAN_STATES_IBGE_CODE_MAP, NFeXML} from "@l10n_br_pos_nfce/js/nfe-xml.esm";

const L10nBrNfceOrder = (Order) =>
    class L10nBrNfceOrder extends Order {
        async document_send(component) {
            if (this.document_type !== "65") {
                return super.document_send(...arguments);
            }

            if (!this.get_partner()) {
                const anonymousPartner = this.pos.db.get_partner_by_id(
                    this.pos.config.partner_id ? this.pos.config.partner_id[0] : false
                );

                if (anonymousPartner) {
                    this.set_partner(anonymousPartner);
                }

                if (component) {
                    component.trigger("close-popup");
                }
            }

            return true;
        }

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
                ...this._buildNFCeAdditionalInfo(),
            };
        }

        _buildNFCeAdditionalInfo() {
            // Mudanças aqui para o padrao do odoo16 e tambem padrao da propria adaptacao
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
        }

        _prepare_fiscal_json(json) {
            if (super._prepare_fiscal_json) {
                super._prepare_fiscal_json(...arguments);
            }

            json.document_type = this.document_type;
        }

        get_total_icms() {
            const orderlines = this.get_orderlines();
            let totalICMS = 0;

            for (const line of orderlines) {
                const productFiscalMap = this.pos.fiscal_map_by_template_id
                    ? this.pos.fiscal_map_by_template_id[line.product.product_tmpl_id]
                    : false;

                if (productFiscalMap && productFiscalMap.icms_cst_code === "00") {
                    totalICMS += parseFloat(productFiscalMap.icms_value) || 0;
                }
            }

            return totalICMS;
        }

        get_total_pis() {
            const orderlines = this.get_orderlines();
            let totalPIS = 0;

            for (const line of orderlines) {
                const productFiscalMap = this.pos.fiscal_map_by_template_id
                    ? this.pos.fiscal_map_by_template_id[line.product.product_tmpl_id]
                    : false;

                if (productFiscalMap) {
                    totalPIS += parseFloat(productFiscalMap.pis_value) || 0;
                }
            }

            return totalPIS;
        }

        get_total_cofins() {
            const orderlines = this.get_orderlines();
            let totalCofins = 0;

            for (const line of orderlines) {
                const productFiscalMap = this.pos.fiscal_map_by_template_id
                    ? this.pos.fiscal_map_by_template_id[line.product.product_tmpl_id]
                    : false;

                if (productFiscalMap) {
                    totalCofins += parseFloat(productFiscalMap.cofins_value) || 0;
                }
            }

            return totalCofins;
        }

        get_total_without_discount() {
            const orderlines = this.get_orderlines();
            let totalWithoutDiscount = 0;

            for (const line of orderlines) {
                totalWithoutDiscount +=
                    (parseFloat(line.product.lst_price) || 0) *
                    (parseFloat(line.quantity) || 0);
            }

            return totalWithoutDiscount;
        }

        get_total_icms_base() {
            const orderlines = this.get_orderlines();
            let totalICMSBase = 0;

            for (const line of orderlines) {
                const productFiscalMap = this.pos.fiscal_map_by_template_id
                    ? this.pos.fiscal_map_by_template_id[line.product.product_tmpl_id]
                    : false;

                if (productFiscalMap && productFiscalMap.icms_cst_code === "00") {
                    totalICMSBase += parseFloat(productFiscalMap.icms_base) || 0;
                }
            }

            return totalICMSBase;
        }
    };

Registries.Model.extend(Order, L10nBrNfceOrder);

const L10nBrNfcePosGlobalState = (PosGlobalState) =>
    class L10nBrNfcePosGlobalState extends PosGlobalState {
        /**
         * Mantém o fluxo antigo de envio de NFC-e,
         * mas usando a API do Odoo 16.
         */
        async push_and_invoice_order(order) {
            if (this.config.simplified_document_type !== "65") {
                return super.push_and_invoice_order(...arguments);
            }

            if (!order.get_partner()) {
                throw {
                    code: 400,
                    message: "Missing Customer",
                    data: {},
                };
            }

            return this.push_single_order(order, {
                timeout: 30000,
                to_invoice: true,
            });
        }

        /**
         * Envio dos pedidos para o backend.
         *
         * O Odoo 16 já possui _save_to_server().
         * Aqui interceptamos apenas quando for NFC-e.
         */
        async _save_to_server(orders, options = {}) {
            if (this.config.simplified_document_type !== "65") {
                return super._save_to_server(...arguments);
            }

            if (!orders || !orders.length) {
                return [];
            }

            const timeout =
                typeof options.timeout === "number"
                    ? options.timeout
                    : 30000 * orders.length;

            const ordersToSync = orders.filter(
                (order) => !this.syncingOrders || !this.syncingOrders.has(order.id)
            );

            if (!ordersToSync.length) {
                return [];
            }

            if (this.syncingOrders) {
                ordersToSync.forEach((order) => {
                    this.syncingOrders.add(order.id);
                });
            }

            this.set_synch("connecting", ordersToSync.length);

            const orderIdsToSync = ordersToSync.map((order) => order.id);

            const args = [
                ordersToSync.map((order) => {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                }),
                options.draft || false,
            ];

            try {
                const serverIds = await this.env.services.rpc(
                    {
                        model: "pos.order",
                        method: "create_from_ui",
                        args: args,
                        kwargs: {
                            context: this.env.session.user_context,
                        },
                    },
                    {
                        timeout: timeout,
                        shadow: !options.to_invoice,
                    }
                );

                for (const orderId of orderIdsToSync) {
                    this.db.remove_order(orderId);

                    if (this.syncingOrders) {
                        this.syncingOrders.delete(orderId);
                    }
                }

                this.failed = false;
                this.set_synch("connected");

                await this._fillNFCeAdditionalInfo(serverIds);

                return serverIds;
            } catch (error) {
                if (this.syncingOrders) {
                    ordersToSync.forEach((order) => {
                        this.syncingOrders.delete(order.id);
                    });
                }

                /*
                 * Se for erro de regra de negócio,
                 * mantém o comportamento padrão.
                 */
                if (
                    error.code === 200 &&
                    (!this.failed || options.show_error) &&
                    !options.to_invoice
                ) {
                    this.failed = error;
                    this.set_synch("error");
                    throw error;
                }

                /*
                 * Se não conseguiu comunicar com o backend,
                 * entra em contingência.
                 */
                this.set_synch("disconnected");

                this._contingenciaNFCe(orders);

                this.failed = true;

                return orders.map((order) => ({
                    pos_reference: order.data.name,
                }));
            }
        }

        /**
         * Recebe do backend as informações da NFC-e autorizada.
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
                console.warn("NFC-e: create_from_ui não retornou account_move.");
                return;
            }

            const moves = await this.env.services.rpc({
                model: "account.move",
                method: "read",
                args: [
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
                    ],
                ],
                kwargs: {
                    context: this.env.session.user_context,
                },
            });

            if (!moves || !moves.length) {
                console.warn(
                    "NFC-e: account.move não encontrado:",
                    orderOption.account_move
                );
                return;
            }

            const move = moves[0];

            console.log("NFC-e ACCOUNT MOVE:", move);
            let supplement = null;

            if (move.fiscal_document_id) {
                const fiscalDocuments = await this.env.services.rpc({
                    model: "l10n_br_fiscal.document",
                    method: "read",
                    args: [[move.fiscal_document_id[0]], ["nfe40_infNFeSupl"]],
                    kwargs: {
                        context: this.env.session.user_context,
                    },
                });

                console.log("NFC-e FISCAL DOCUMENT:", fiscalDocuments);

                if (fiscalDocuments.length && fiscalDocuments[0].nfe40_infNFeSupl) {
                    const supplementId = fiscalDocuments[0].nfe40_infNFeSupl[0];

                    const supplements = await this.env.services.rpc({
                        model: "l10n_br_fiscal.document.supplement",
                        method: "read",
                        args: [[supplementId], ["qrcode", "url_key"]],
                        kwargs: {
                            context: this.env.session.user_context,
                        },
                    });

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

            console.log("NFC-e CURRENT ORDER:", currentOrder);
        }

        /**
         * Contingência.
         *
         * OBS:
         * O mecanismo antigo utilizava
         * nfce_document_serie_sequence_number_next,
         * que foi removido no Odoo 16.
         *
         * Por enquanto deixamos a estrutura preparada,
         * sem tentar alterar a sequence do backend pelo
         * navegador.
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

            /*
             * O número precisa ser fornecido pelo backend
             * no Odoo 16. Não usamos mais o campo antigo
             * nfce_document_serie_sequence_number_next.
             */
            for (let i = 0; i < orders.length; i++) {
                const currentOrder = this.get_order();

                if (!currentOrder || currentOrder.document_number) {
                    continue;
                }

                /*
                 * Se o pedido já recebeu número do backend,
                 * usamos ele.
                 *
                 * Caso contrário, não inventamos um número
                 * local para evitar colisão de sequence.
                 */
                if (!currentOrder.document_number) {
                    console.warn("NFC-e em contingência: número ainda não disponível.");
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
        }

        async _qrCodeNFCeContingency(currentOrder, chaveEdoc) {
            const xml = new NFeXML(this, currentOrder, chaveEdoc);

            currentOrder.qr_code = await xml.generateQRCodeText();
        }
    };

Registries.Model.extend(PosGlobalState, L10nBrNfcePosGlobalState);
