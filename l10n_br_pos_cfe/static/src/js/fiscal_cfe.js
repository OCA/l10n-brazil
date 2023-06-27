odoo.define("l10n_br_pos_cfe.FiscalDocumentCFe", function (require) {
    "use strict";

    var Session = require("web.Session");
    var core = require("web.core");
    const {Gui} = require("point_of_sale.Gui");
    var _t = core._t;

    // IMPROVEMENT: This is too much. We can get away from this class.
    class FiscalDocumentResult {
        constructor({successful, message, response, traceback}) {
            this.successful = successful;
            this.message = message;
            this.response = response;
            this.traceback = traceback;
        }
    }

    class FiscalDocumentResultGenerator {
        IoTActionError(message_body) {
            return new FiscalDocumentResult({
                successful: false,
                message: {
                    title: _t("Erro ao se comunicar com a inteface fiscal"),
                    body: message_body,
                },
                traceback: true,
            });
        }
        IoTResultError(message_body) {
            return new FiscalDocumentResult({
                successful: false,
                message: {
                    title: _t("Falha ao se comunicar com a inteface fiscal"),
                    body: message_body,
                },
                traceback: false,
            });
        }
        Successful(response) {
            return new FiscalDocumentResult({
                successful: true,
                response: response,
            });
        }
    }

    var FiscalDocumentMixin = {
        init: function (pos) {
            this.fiscal_queue = [];
            this.fiscalDocumentResultGenerator = new FiscalDocumentResultGenerator();
            this.pos = pos;
        },
        send_order: async function (order) {
            if (order) {
                this.fiscal_queue.push(order);
            }
            let sendFiscalResult = null;
            let sendFiscalResultParsed = null;

            while (this.fiscal_queue.length > 0) {
                const order_to_send = this.fiscal_queue.shift();
                if (
                    order_to_send.document_session_number &&
                    this.pos.last_document_session_number ===
                        order_to_send.document_session_number
                ) {
                    //  TODO: Melhorar esse método, consultando os dados da sessão em questão.
                    return this.fiscalDocumentResultGenerator.IoTActionError(
                        _t("Documento já transmitido.")
                    );
                }
                var order_json = order_to_send.export_for_printing();

                try {
                    sendFiscalResult = await this.send_order_job(order_json);
                } catch (error) {
                    // Error in communicating to the IoT box.
                    this.fiscal_queue.length = 0;
                    return this.fiscalDocumentResultGenerator.IoTActionError(error);
                }

                try {
                    sendFiscalResultParsed = JSON.parse(sendFiscalResult);
                } catch (error) {
                    // Error in communicating to the IoT box.
                    this.fiscal_queue.length = 0;
                    return this.fiscalDocumentResultGenerator.IoTResultError(
                        sendFiscalResult
                    );
                }

                // Rpc call is okay but iot failed because
                // IoT box can't find a printer.
                if (!sendFiscalResult || sendFiscalResult.result === false) {
                    this.fiscal_queue.length = 0;
                    return this.fiscalDocumentResultGenerator.IoTResultError();
                }
            }
            return this.fiscalDocumentResultGenerator.Successful(
                sendFiscalResultParsed
            );
        },

        session_number: async function () {
            let sendFiscalResult = null;
            let sendFiscalResultParsed = null;
            try {
                sendFiscalResult = await this.session_number_job();
            } catch (error) {
                // Error in communicating to the IoT box.
                return this.fiscalDocumentResultGenerator.IoTActionError(error);
            }
            try {
                sendFiscalResultParsed = JSON.parse(sendFiscalResult);
            } catch (error) {
                // Error in communicating to the IoT box.
                return this.fiscalDocumentResultGenerator.IoTResultError(
                    sendFiscalResult
                );
            }
            // Rpc call is okay but iot failed because
            // IoT box can't find a printer.
            if (!sendFiscalResult || sendFiscalResult.result === false) {
                this.fiscal_queue.length = 0;
                return this.fiscalDocumentResultGenerator.IoTResultError();
            }

            return this.fiscalDocumentResultGenerator.Successful(
                sendFiscalResultParsed
            );
        },

        cancel_order: async function (order) {
            let sendFiscalResult = null;
            // Const sendFiscalResultParsed = null;
            const order_json = {
                order_id: order.backendId,
                chaveConsulta: order.document_key,
                doc_destinatario: order.cnpj_cpf,
                xml_cfe_venda: order.authorization_file,
                xml_cfe_cacelada: order.cancel_file,
                cnpj_software_house: order.pos.config.cnpj_software_house,
            };

            try {
                sendFiscalResult = await this.cancel_order_job(order_json);
            } catch (error) {
                // Error in communicating to the IoT box.
                return this.fiscalDocumentResultGenerator.IoTActionError(error);
            }

            // Esse trecho deve ser removido.
            if (!sendFiscalResult) {
                return this.fiscalDocumentResultGenerator.IoTResultError();
            }

            return this.fiscalDocumentResultGenerator.Successful(sendFiscalResult);
            // Fim do trecho a ser removido.

            // A API do IOT esta retornando fora do padrão, por isso o código abaixo
            // esta comentado, deve ser alterádo lá para que aqui fique padronizado.

            // try {
            //     sendFiscalResultParsed = JSON.parse(sendFiscalResult);
            // } catch (error) {
            //     // Error in communicating to the IoT box.
            //     return this.fiscalDocumentResultGenerator.IoTResultError(
            //         sendFiscalResult
            //     );
            // }

            // // Rpc call is okay but iot failed because
            // // IoT box can't find a printer.
            // if (!sendFiscalResult || sendFiscalResult.result === false) {
            //     return this.fiscalDocumentResultGenerator.IoTResultError();
            // }

            // return this.fiscalDocumentResultGenerator.Successful(
            //     sendFiscalResultParsed
            // );
        },
        // Print_order: async function (order) {},
        _onIoTActionResult: function (data) {
            if (this.pos && (data === false || data.result === false)) {
                Gui.showPopup("ErrorPopup", {
                    title: _t("Connection to the Fiscal Interface failed"),
                    body: _t(
                        "Please check if the Fiscal Interface is still connected."
                    ),
                });
            }
        },

        _onIoTActionFail: function () {
            if (this.pos) {
                Gui.showPopup("ErrorPopup", {
                    title: _t("Connection to Fiscal Interface failed"),
                    body: _t(
                        "Please check if the Fiscal Interface is still connected."
                    ),
                });
            }
        },
    };

    var FiscalDocumentCFe = core.Class.extend(FiscalDocumentMixin, {
        init: function (url, pos) {
            FiscalDocumentMixin.init.call(this, pos);
            this.connection = new Session(undefined, url || "http://localhost:8069", {
                use_cors: true,
            });
            this.cfe_config = {
                sat_path: pos.config.sat_path,
                codigo_ativacao: pos.config.activation_code,
                impressora: pos.config.printer,
                printer_params: pos.config.printer_params,
                fiscal_printer_type: pos.config.fiscal_printer_type,
                assinatura: pos.config.signature_sat,
            };
            const hw_fiscal = this.pos.proxy.get("status").drivers.hw_fiscal;
            if (hw_fiscal && hw_fiscal.status !== "connect") {
                this.init_job();
            }
        },

        init_job: function () {
            return this.connection.rpc("/hw_proxy/init", {
                json: this.cfe_config,
            });
        },

        session_number_job: function (order) {
            return this.connection.rpc("/hw_proxy/sessao_sat", {
                json: {json: order},
            });
        },

        send_order_job: function (order_json) {
            return this.connection.rpc("/hw_proxy/enviar_cfe_sat", {
                json: order_json,
            });
        },

        cancel_order_job: function (order_json) {
            return this.connection.rpc("/hw_proxy/cancelar_cfe", {
                json: order_json,
            });
        },

        print_order_job: function (order_json) {
            return this.connection.rpc("/hw_proxy/reprint_cfe", {
                json: order_json,
            });
        },
    });

    return {
        FiscalDocumentMixin: FiscalDocumentMixin,
        FiscalDocumentCFe: FiscalDocumentCFe,
        FiscalDocumentResult,
        FiscalDocumentResultGenerator,
    };
});
