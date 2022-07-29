/*
    L10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_br_tef.devices", function (require) {
    "use strict";

    const core = require("web.core");
    let ls_transaction_global_value = "";

    /**
     Necessary TAGs for integration.
     */
    class TagsDestaxa {
        fill_tags(as_tag, as_value) {
            if (as_tag === "automacao_coleta_opcao")
                this.automacao_coleta_opcao = as_value;
            else if (as_tag === "automacao_coleta_informacao")
                this.automacao_coleta_informacao = as_value;
            else if (as_tag === "automacao_coleta_mensagem")
                this.automacao_coleta_mensagem = as_value;
            else if (as_tag === "automacao_coleta_retorno")
                this.automacao_coleta_retorno = as_value;
            else if (as_tag === "automacao_coleta_sequencial")
                this.automacao_coleta_sequencial = as_value;
            else if (as_tag === "transacao_comprovante_1via")
                this.transacao_comprovante_1via = as_value;
            else if (as_tag === "transacao_comprovante_2via")
                this.transacao_comprovante_2via = as_value;
            else if (as_tag === "transacao_comprovante_resumido")
                this.transacao_comprovante_resumido = as_value;
            else if (as_tag === "servico") this.servico = as_value;
            else if (as_tag === "transacao") this.transacao = as_value;
            else if (as_tag === "transacao_produto") this.transacao_produto = as_value;
            else if (as_tag === "retorno") this.retorno = as_value;
            else if (as_tag === "mensagem") this.mensagem = as_value;
            else if (as_tag === "sequencial") this.sequencial = parseInt(as_value, 0);
            else if (as_tag === "automacao_coleta_palavra_chave")
                this.automacao_coleta_palavra_chave = as_value;
            else if (as_tag === "automacao_coleta_tipo")
                this.automacao_coleta_tipo = as_value;
            else if (as_tag === "estado") this.estado = as_value;
            else if (as_tag === "aplicacao_tela") this.aplicacao_tela = as_value;
        }

        initialize_tags() {
            this.transacao_comprovante_1via = "";
            this.transacao_comprovante_2via = "";
            this.transacao = "";
            this.transacao_produto = "";
            this.servico = "";
            this.retorno = 0;
            this.sequencial = 0;
        }

        increment_sequential() {
            this.sequencial += 1;
            return this.sequencial;
        }
    }

    const TefProxy = core.Class.extend({
        actions: ["product", "cashier", "client"],
        init: function (attributes) {
            this.pos = attributes.pos;
            this.debit_server = this.pos.config.debit_server;
            this.credit_server = this.pos.config.credit_server;
            this.funding_institution = this.pos.config.institution_selection;
            this.environment = this.pos.config.environment_selection;
            this.ws_connection = null;
            this.connect_init = false;
            this.transaction_queue = [];
            this.tags = new TagsDestaxa();

            this.plots = 1;
            this.in_sequential_execute = 0;
            this.transaction_method = "";
            this.operation = "";

            this.debug_card = null;
            this.cancelation_info = null;

            this.connect();
        },
        set_connected: function () {
            this.pos.set({tef_status: {state: "connected", pending: 0}});
        },
        set_connecting: function () {
            this.pos.set({tef_status: {state: "connected", pending: 0}});
        },
        set_warning: function () {
            this.pos.set({tef_status: {state: "warning", pending: 0}});
        },
        set_disconnected: function () {
            this.pos.set({tef_status: {state: "disconnected", pending: 0}});
        },
        set_error: function () {
            this.pos.set({tef_status: {state: "error", pending: 0}});
        },
        connect: function () {
            const self = this;
            // Returns the established connection.
            try {
                if (
                    (this.ws_connection && this.ws_connection.readyState !== 1) ||
                    this.ws_connection === null
                )
                    this.ws_connection = new WebSocket("ws://localhost:60906");

                if (this.ws_connection.readyState === 3) return;

                // Opens the connection and sends the first service
                this.ws_connection.onopen = function () {
                    self.connect_init = true;
                    // Reports that you are connected.
                    self.set_connected();
                    self.trace("Connection successful");
                    // Initialize the tags for integration.
                    self.tags.initialize_tags();
                    self.consult();
                };

                /**
                 Function for handling connection closed.
                 */
                this.ws_connection.onclose = () => {
                    self.trace("Connection closed");
                    self.set_disconnected();
                    self.connect_init = false;
                    self.ws_connection.close();
                    self.abort();
                };

                /**
                 Function for handling communication errors.
                 */
                this.ws_connection.onerror = (error) => {
                    self.trace(error.data);
                    self.set_warning();
                    self.connect_init = false;
                    self.ws_connection.close();
                };

                /**
                 Function for receiving messages.
                 */
                this.ws_connection.onmessage = (e) => {
                    self.set_connecting();
                    // Shows the message.
                    self.trace("Received >>> " + e.data);

                    // Initializes Tags.
                    self.tags.initialize_tags();

                    // Show the received Tags.
                    self.disassembling_service(e.data);

                    // FIXME: Check if need to keep the in_sequence in addition to the sequence in the tags object
                    // // If 'retorno' isn't OK
                    // if (this.tags.retorno !== "0") {
                    //     in_sequential = this.tags.sequencial;
                    // }

                    // Saves the current sequence of the collection.
                    this.in_sequential_execute = this.tags.automacao_coleta_sequencial;
                    setTimeout(function () {
                        // Initial Checks
                        if (self.check_completed_consult()) return;
                        if (self.check_completed_execution()) return;
                        if (self.check_completed_start()) return;
                        if (self.check_cancelled_transaction()) return;

                        // Cancellation Operations
                        if (self.check_user_access()) return;
                        if (self.check_user_password()) return;
                        if (self.check_purchase_date()) return;
                        if (self.check_document_number()) return;

                        // Credit without PinPad
                        // Only works if card_number is filled in Debug mode
                        if (this.debug_card) {
                            if (self.check_completed_start_execute()) return;
                            if (self.check_transaction_card_number()) return;
                            if (self.check_type_card_number()) return;
                            if (self.check_completed_send_card_number()) return;
                            if (self.check_completed_send_expiring_date()) return;
                        }

                        if (self.check_completed_send_security_code()) return;
                        if (self.check_authorized_operation()) return;

                        // Credit with PinPad
                        // check_completed_send();
                        if (self.check_inserted_card()) return;
                        if (self.check_filled_value()) return;
                        self.check_filled_value_send();

                        if (self.check_payment_method()) return;
                        if (self.check_institution()) return;
                        if (self.check_plots()) return;

                        if (self.check_inserted_password()) return;

                        // Debit with PinPad
                        if (self.check_withdrawal_amount()) return;

                        // Final checks
                        if (self.check_approved_transaction()) return;
                        if (self.check_removed_card()) return;
                        if (self.finishes_operation()) return;

                        // Cancellation checks
                        if (self.check_request_confirmation()) return;
                        if (self.check_approval_request()) return;
                        if (self.check_chip_processing()) return;
                        if (self.check_cancellation_ok()) return;
                        if (self.check_cancellation_remove_card()) return;
                        if (self.check_cancellation_finishes()) return;

                        // Checking for final errors
                        if (self.check_for_errors()) return;
                    }, 1000);
                };
            } catch (err) {
                console.log("Could not connect to server");
                this.set_error();
            }
        },

        check_withdrawal_amount: function () {
            if (this.tags.automacao_coleta_mensagem === "Valor do Saque") {
                this.collect("0");
                return true;
            }
            return false;
        },

        check_authorized_operation: function () {
            // Authorized operation -- Without PinPad
            if (this.tags.automacao_coleta_mensagem === "Transacao autorizada") {
                const transaction_value = this.pos.get("selectedOrder")
                    .selected_paymentline.amount;
                this.collect("", transaction_value);

                this.screenPopupPagamento("Transação Aprovada");

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
            // Authorized operation -- With PinPad
            else if (this.tags.mensagem === "Transacao autorizada") {
                this.screenPopupPagamento("Transação Aprovada");

                confirm(this.tags.sequencial);
                this.tags.mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_removed_card: function () {
            const self = this;
            if (
                this.tags.servico == "executar" &&
                this.tags.mensagem &&
                this.tags.mensagem === "Transacao aprovada, RETIRE O CARTAO"
            ) {
                self.confirm(this.tags.sequencial);

                setTimeout(function () {
                    self.screenPopupPagamento("Retire o Cartão");
                }, 1500);

                this.tags.mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_approval_request: function () {
            if (
                this.tags.automacao_coleta_mensagem ===
                "SOLICITANDO AUTORIZACAO, AGUARDE ..."
            ) {
                this.collect("");

                this.screenPopupPagamento("Solicitando Autorização");

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_chip_processing: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Processando o cartao com CHIP"
            ) {
                this.collect("");

                this.screenPopupPagamento(
                    "Processando o cartao com CHIP... Por Favor, Insira a Senha."
                );

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_cancellation_ok: function () {
            if (this.tags.automacao_coleta_mensagem === ">CANCELAMENTO OK") {
                this.collect("");

                this.screenPopupPagamento("Cancelamento Autorizado!!!");

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_cancellation_remove_card: function () {
            const self = this;
            if (this.tags.mensagem === ">CANCELAMENTO OK, RETIRE O CARTAO") {
                confirm(this.tags.sequencial);

                setTimeout(function () {
                    self.screenPopupPagamento("Retire o Cartão");
                }, 1500);

                this.tags.mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_cancellation_finishes: function () {
            const self = this;
            if (
                this.tags.retorno == "1" &&
                this.tags.servico == "executar" &&
                this.tags.transacao == "Administracao Cancelar"
            ) {
                self.finish();

                self.pos.gui.current_popup.hide();

                this.tags.transacao = "";
                setTimeout(function () {
                    self.consult();
                }, 2000);
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_inserted_password: function () {
            if (
                this.tags.automacao_coleta_mensagem ===
                "Aguarde !!! Processando a transacao ..."
            ) {
                this.collect("");

                this.screenPopupPagamento("Processing the transaction...");

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_approved_transaction: function () {
            if (
                this.tags.automacao_coleta_mensagem &&
                this.tags.automacao_coleta_mensagem == "Transacao aprovada" &&
                this.tags.servico == "" &&
                this.tags.transacao == ""
            ) {
                this.screenPopupPagamento("Transaction Approved");
                this.collect("");

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_completed_start_execute: function () {
            /*
             * Message sequence to switch to manual card data input flow
             */
            if (
                this.tags.automacao_coleta_palavra_chave ===
                    "transacao_cartao_numero" &&
                this.tags.automacao_coleta_retorno === "0" &&
                this.tags.automacao_coleta_mensagem === "INSIRA OU PASSE O CARTAO"
            ) {
                this.send(
                    'automacao_coleta_sequencial="' +
                        this.in_sequential_execute +
                        '"automacao_coleta_retorno="0"'
                );
                setTimeout(() => {
                    this.send(
                        'automacao_coleta_sequencial="' +
                            this.in_sequential_execute +
                            '"automacao_coleta_retorno="9"'
                    );
                }, 1000);

                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_transaction_card_number: function () {
            /*
             * Confirm the option to manually enter card data
             */
            if (
                this.tags.automacao_coleta_palavra_chave ===
                    "transacao_cartao_numero" &&
                this.tags.automacao_coleta_tipo === "X" &&
                this.tags.automacao_coleta_retorno === "0" &&
                this.tags.automacao_coleta_mensagem === "<SIM> CANCELAR, <NAO> LER"
            ) {
                this.collect("Digitar");

                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_type_card_number: function () {
            /*
             * Send card number
             */
            if (
                this.tags.automacao_coleta_palavra_chave ===
                    "transacao_cartao_numero" &&
                this.tags.automacao_coleta_tipo === "N" &&
                this.tags.automacao_coleta_retorno === "0" &&
                this.tags.automacao_coleta_mensagem === "Digite o numero do cartao"
            ) {
                this.collect(this.debug_card.card_number);

                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_completed_send_security_code: function () {
            if (
                this.tags.automacao_coleta_palavra_chave == "transacao_valor" &&
                this.tags.automacao_coleta_tipo == "N" &&
                this.tags.automacao_coleta_retorno == "0"
            ) {
                // Send the value
                let transaction_value;
                if (
                    this.cancelation_info &&
                    this.cancelation_info.cancellation_transaction_value
                ) {
                    transaction_value = this.cancelation_info
                        .cancellation_transaction_value;
                } else {
                    transaction_value = this.pos.get("selectedOrder")
                        .selected_paymentline.amount;
                }
                this.collect("", transaction_value);

                // Reset the Value
                ls_transaction_global_value = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_retorno = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_completed_execution: function () {
            if (
                this.tags.automacao_coleta_palavra_chave ===
                    "transacao_cartao_numero" &&
                this.tags.automacao_coleta_tipo != "N" &&
                this.tags.automacao_coleta_retorno == "0" &&
                !this.debug_card
            ) {
                this.collect("");

                this.screenPopupPagamento("Please, insert the Card");

                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_retorno = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_filled_value: function () {
            if (this.tags.automacao_coleta_mensagem == "AGUARDE A SENHA") {
                this.collect("");

                this.screenPopupPagamento("Please, enter the password");

                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_request_confirmation: function () {
            if (
                this.tags.automacao_coleta_mensagem &&
                this.tags.automacao_coleta_mensagem.indexOf(
                    "Confirma o cancelamento desta transacao"
                ) > -1 &&
                this.tags.automacao_coleta_tipo === "X"
            ) {
                this.pos.gui.show_popup("ConfirmaCancelamentoCompraPopup", {
                    title: _t("Purchase Information"),
                    body: _t(this.tags.automacao_coleta_mensagem),
                });

                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_mensagem = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        finishes_operation: function () {
            const self = this;
            if (
                this.tags.retorno == "1" &&
                this.tags.servico == "executar" &&
                this.tags.transacao == "Cartao Vender"
            ) {
                self.finish();
                self.complete_paymentline();

                self.pos.gui.current_popup.hide();

                this.tags.transacao = "";
                setTimeout(function () {
                    self.consult();
                }, 2000);
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        disable_order_transaction: function () {
            const payment_screen = this.pos.gui.current_screen;
            const order = this.pos.get_order();
            if (order) {
                order.tef_in_transaction = false;
                payment_screen.order_changes();
            }
        },

        complete_paymentline: function () {
            this.disable_order_transaction();
            const payment_screen = this.pos.gui.current_screen;
            const selected_paymentline = payment_screen.get_selected_paymentline();
            if (selected_paymentline) {
                selected_paymentline.tef_payment_completed = true;
                payment_screen.render_paymentlines();
            }
        },

        clearCancelamentoCompraPopup: function () {
            const modal_inputs = $(".modal-body input");
            const modal_inputs_length = modal_inputs.length;

            for (let i = 0; i < modal_inputs_length; i++) {
                modal_inputs[i].value = "";
            }
        },

        abort: function () {
            const self = this;

            if (self.pos.gui.current_popup) {
                self.pos.gui.current_popup.hide();
                self.clearCancelamentoCompraPopup();
                this.cancelation_info = null;
            }
            setTimeout(function () {
                self.send(
                    'automacao_coleta_retorno="9"automacao_coleta_mensagem="Fluxo Abortado pelo operador!!"automacao_coleta_sequencial="' +
                        self.in_sequential_execute +
                        '"'
                );
            }, 1000);

            setTimeout(function () {
                if (self.pos.gui.current_popup) {
                    self.pos.gui.current_popup.hide();
                }
            }, 3000);
        },

        redo_operation: function (sequential_return) {
            const self = this;
            if (this.transaction_queue.length > 0) {
                setTimeout(function () {
                    self.transaction_queue[
                        self.transaction_queue.length - 1
                    ] = self.transaction_queue[
                        self.transaction_queue.length - 1
                    ].replace(
                        /sequencial="\d+"/,
                        'sequencial="' + sequential_return + '"'
                    );
                    self.send(
                        self.transaction_queue[self.transaction_queue.length - 1]
                    );
                }, 1000);
            }
        },

        check_completed_consult: function () {
            if (this.tags.servico == "consultar" && this.tags.retorno == "0") {
                return true;
            } else if (
                this.tags.automacao_coleta_mensagem !=
                    "Fluxo Abortado pelo operador!!" &&
                this.tags.servico == "" &&
                this.tags.retorno != "0" &&
                !this.tags.mensagem
            ) {
                this.redo_operation(this.tags.sequencial);
                return false;
            }
                return false;

        },

        check_cancelled_transaction: function () {
            if (this.tags.automacao_coleta_mensagem === "Transacao cancelada") {
                this.disable_order_transaction();
                return true;
            }
                return false;

        },

        screenPopupPagamento: function (msg) {
            console.log(msg);
            this.pos.gui.show_popup("StatusPagementoPopUp", {
                title: _t("Please, wait!"),
                body: _t(msg),
            });
        },

        check_completed_start: function () {
            if (
                this.tags.servico == "iniciar" &&
                this.tags.retorno == "1" &&
                this.tags.aplicacao_tela == "VBIAutomationTest"
            ) {
                /*
                 * TODO: Check how an installment purchase is made at the POS.
                 *  The query below does not currently select any elements in the POS.
                 ? Does this installment information on the payment line appear when enabling some settings?
                 */
                const payment_term = $(".paymentline-input.payment_term").get("0");
                if (payment_term) {
                    this.plots = payment_term.options[
                        payment_term.selectedIndex
                    ].text.match(/\d+/);
                    if (this.plots) this.plots = parseInt(this.plots[0]);
                    else this.plots = 1;
                }

                if (!this.funding_institution && this.plots > 1) {
                    this.pos.gui.show_popup("error", {
                        title: "No type of installment scheme selected!",
                        body:
                            "You must select at least one institution in the POS settings",
                    });
                    return false;
                }
                this.execute();
                this.screenPopupPagamento("Initializing Operation");
                this.tags.aplicacao_tela = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_user_access: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Usuario de acesso" &&
                this.tags.automacao_coleta_tipo === "X" &&
                this.tags.automacao_coleta_palavra_chave ===
                    "transacao_administracao_usuario"
            ) {
                this.pos.gui.show_popup("CancelamentoCompraPopup", {});
                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        _get_cancel_date: function (date) {
            let transaction_date = "";
            if (date) {
                transaction_date =
                    (date.getDate() < 10 ? "0" + date.getDate() : date.getDate()) +
                    "/" +
                    (date.getMonth() + 1 < 10
                        ? "0" + (date.getMonth() + 1)
                        : date.getMonth() + 1) +
                    "/" +
                    date.getFullYear().toString().substring(2, 5);
            }
            return transaction_date;
        },

        proceed_cancellation: function () {
            // TODO: Make the cancel popup pass this info through function parameters
            this.cancelation_info = {
                cancellation_user: $(".CancelamentoCompraPopup_usuario").val(),
                cancellation_password: $(".CancelamentoCompraPopup_senha").val(),
                cancellation_document_number: $(
                    ".CancelamentoCompraPopup_documento"
                ).val(),
                cancellation_transaction_value: $(
                    ".CancelamentoCompraPopup_valor"
                ).val(),
                cancellation_transaction_date: this._get_cancel_date(
                    new Date($(".CancelamentoCompraPopup_data").val())
                ),
            };

            const cancellation_tags =
                'transacao_tipo_cartao=""transacao_pagamento=""transacao_produto=""';
            this.send(
                'automacao_coleta_sequencial="' +
                    this.in_sequential_execute +
                    '"automacao_coleta_retorno="0"automacao_coleta_informacao="' +
                    this.cancelation_info.cancellation_user +
                    '"' +
                    cancellation_tags
            );

            this.clearCancelamentoCompraPopup();
        },

        confirm_proceed_cancellation: function (proceed) {
            const transaction_value = proceed ? "Sim" : "Nao";
            this.collect("", transaction_value);
        },

        check_user_password: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Senha de acesso" &&
                this.tags.automacao_coleta_tipo === "X" &&
                this.tags.automacao_coleta_palavra_chave ===
                    "transacao_administracao_senha"
            ) {
                this.collect("", this.cancelation_info.cancellation_password);

                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                return false;

        },

        check_purchase_date: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Data Transacao Original" &&
                this.tags.automacao_coleta_tipo === "D" &&
                this.tags.automacao_coleta_palavra_chave === "transacao_data"
            ) {
                this.collect("", this.cancelation_info.cancellation_transaction_date);

                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                return false;

        },

        check_document_number: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Numero do Documento" &&
                this.tags.automacao_coleta_tipo === "N" &&
                this.tags.automacao_coleta_palavra_chave === "transacao_nsu"
            ) {
                this.collect("", this.cancelation_info.cancellation_document_number);

                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                return false;

        },

        check_payment_method: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Forma de Pagamento" &&
                this.tags.automacao_coleta_palavra_chave === "transacao_pagamento" &&
                this.tags.automacao_coleta_tipo === "X"
            ) {
                this.collect(this.transaction_method);
                this.screenPopupPagamento("Payment " + this.transaction_method);
                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_institution: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Financiado pelo" &&
                this.tags.automacao_coleta_palavra_chave === "transacao_financiado" &&
                this.tags.automacao_coleta_tipo === "X"
            ) {
                this.collect(this.funding_institution);
                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_plots: function () {
            if (
                this.tags.automacao_coleta_mensagem === "Parcelas" &&
                this.tags.automacao_coleta_palavra_chave === "transacao_parcela" &&
                this.tags.automacao_coleta_tipo === "N"
            ) {
                this.collect(this.plots);
                this.screenPopupPagamento("Payment in " + this.plots + " installments");
                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },

        check_for_errors: function () {
            // Here all the exceptions will be handle

            // For any other exceptions, just abort the operation
            if (
                this.tags.automacao_coleta_retorno === "9" &&
                this.tags.automacao_coleta_mensagem ===
                    "Fluxo Abortado pelo operador!!" &&
                this.tags.retorno != "2"
            ) {
                return true;
            } else if (
                this.tags.automacao_coleta_mensagem === "Digite o numero do cartao"
            ) {
                this.screenPopupPagamento("Erro - PinPad não conectado!!!");
                this.abort();
            } else if (
                this.tags.automacao_coleta_mensagem ===
                "TRANSACAO ORIGINAL NAO LOCALIZADA"
            ) {
                this.screenPopupPagamento(
                    "Erro - Transação Original não Localizada!!!"
                );
                this.abort();
            } else if (this.tags.automacao_coleta_mensagem === "Problema na conexao") {
                this.screenPopupPagamento("Erro - Problema na Conexão!!!");
                this.abort();
            } else if (
                (this.tags.automacao_coleta_mensagem || false) &&
                this.tags.automacao_coleta_mensagem.startsWith("Transacao cancelada")
            ) {
                this.tags.automacao_coleta_mensagem = "";
                return true;
            } else if (
                this.tags.automacao_coleta_mensagem === "INSIRA OU PASSE O CARTAO"
            ) {
                return true;
            } else if (this.tags.automacao_coleta_mensagem === "RETIRE O CARTAO") {
                this.screenPopupPagamento("Operação Cancelada - Retire o Cartão!!!");
                return true;
            } else if (this.tags.servico === "finalizar") {
                return true;
            } else if (this.tags.servico === "iniciar") {
                return true;
            } else if (
                this.tags.mensagem &&
                this.tags.mensagem.startsWith("Sequencial invalido")
            ) {
                this.tags.mensagem = "";
                this.redo_operation(this.tags.sequencial);
                return true;
            } else {
                const message = this.tags.message || this.tags.automacao_coleta_mensagem;
                if (message) this.screenPopupPagamento(message);
                this.abort();
            }
        },

        execute: function () {
            let ls_execute_tags =
                'servico="executar"retorno="1"sequencial="' +
                this.tags.increment_sequential() +
                '"';
            let ls_payment_transaction = "";
            let ls_card_type = "";
            let ls_product_type = "";
            let ls_transaction_type = "";

            const selected_payment_line = this.pos.gui.current_screen.get_selected_paymentline();

            if (this.operation === "purchase") {
                ls_transaction_type = "Cartao Vender";

                const payment_type =
                    selected_payment_line.cashregister.journal.tef_payment_mode;

                if (payment_type === "01") {
                    ls_card_type = "Credito";
                } else if (payment_type === "02") {
                    ls_card_type = "Debito";
                } else {
                    ls_card_type = "";
                }

                if (this.environment === "Homologacao")
                    ls_product_type =
                        payment_type === "01" ? this.credit_server : this.debit_server;
                if (this.environment === "Producao")
                    // TODO: Verificar porque está hardcoded 'MASTERCARD'
                    ls_product_type = "MASTERCARD";
            } else if (this.operation === "cancellation") {
                ls_transaction_type = "Administracao Cancelar";
            }

            if (this.plots > 1) {
                if (this.funding_institution === "Administradora")
                    this.transaction_method = "2-Financ.Adm.";
                else if (this.funding_institution === "Estabelecimento")
                    this.transaction_method = "3-Financ.Loja";
            } else {
                this.transaction_method = "A vista";
            }

            // TODO: Check in which flow it is necessary to pass the field "transacao_valor" filled in
            if (ls_transaction_global_value !== "") {
                ls_transaction_global_value =
                    'transacao_valor="' + ls_transaction_global_value + '"';
                ls_execute_tags += ls_transaction_global_value;
            }

            if (ls_transaction_type !== "") {
                ls_transaction_type = 'transacao="' + ls_transaction_type + '"';
                ls_execute_tags += ls_transaction_type;
            }

            if (ls_card_type !== "") {
                ls_card_type = 'transacao_tipo_cartao="' + ls_card_type + '"';
                ls_execute_tags += ls_card_type;
            }

            if (ls_payment_transaction !== "") {
                ls_payment_transaction =
                    'transacao_pagamento="' + ls_payment_transaction + '"';
                ls_execute_tags += ls_payment_transaction;
            }

            if (ls_product_type !== "") {
                ls_product_type = 'transacao_produto="' + ls_product_type + '"';
                ls_execute_tags += ls_product_type;
            }

            this.send(ls_execute_tags);
        },

        consult: function () {
            this.send(
                'servico="consultar"retorno="0"sequencial="' +
                    this.tags.increment_sequential() +
                    '"'
            );

            setTimeout(function () {
                if (self.posmodel.gui.current_popup) {
                    self.posmodel.gui.current_popup.hide();
                }
            }, 1000);
        },

        check_completed_send_card_number: function () {
            if (
                this.tags.automacao_coleta_palavra_chave ==
                    "transacao_cartao_validade" &&
                this.tags.automacao_coleta_tipo == "D" &&
                this.tags.automacao_coleta_retorno == "0"
            ) {
                // Send the card expiring date
                this.collect(this.debug_card.card_expiring_date);

                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_retorno = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },
        check_completed_send_expiring_date: function () {
            if (
                this.tags.automacao_coleta_palavra_chave ==
                    "transacao_cartao_codigo_seguranca" &&
                this.tags.automacao_coleta_tipo == "X" &&
                this.tags.automacao_coleta_retorno == "0"
            ) {
                // Send the card security code
                this.collect(this.debug_card.card_security_code);

                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_retorno = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },
        check_completed_send: function () {
            if (this.tags.automacao_coleta_retorno == "0") {
                // Here the user must insert the card

                this.tags.automacao_coleta_retorno = "";
                return true;
            }
                // Handle Exceptions Here
                return false;

        },
        check_inserted_card: function () {
            if (
                this.tags.automacao_coleta_palavra_chave === "transacao_valor" &&
                this.tags.automacao_coleta_tipo != "N"
            ) {
                // Transaction Value
                const transaction_value = this.pos.get("selectedOrder")
                    .selected_paymentline.amount;

                this.collect("", transaction_value);

                this.screenPopupPagamento("Starting Operation");

                // Reset the Value
                ls_transaction_global_value = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_retorno = "";
                return true;
            }
                return false;

        },
        check_filled_value_send: function () {
            // Here the user must enter his password
        },
        trace: function (as_buffer) {
            if (this.pos.debug) {
                console.log(as_buffer);
            }
        },
        disassembling_service: function (to_service) {
            let ln_start = 0;
            const ln_end = to_service
                .toString()
                .indexOf("\n\r\n\t\t\r\n\t\t\t\r\n\t\t\r\n\t");
            let ls_tag = "";
            let ls_value = "";

            try {
                // While reading the received packet isn't finished ...
                while (ln_start < ln_end) {
                    // Recovers the TAG..
                    ls_tag = to_service
                        .toString()
                        .substring(ln_start, to_service.indexOf('="', ln_start));
                    ln_start = ln_start + ls_tag.toString().length + 2;

                    ls_value = to_service
                        .toString()
                        .substring(
                            ln_start,
                            (ln_start = to_service.toString().indexOf('"\n', ln_start))
                        );

                    ln_start += 2;

                    this.tags.fill_tags(ls_tag, ls_value);
                }
            } catch (err) {
                alert("Internal Error: " + err.message);
            }
        },
        collect: function (ao_event, transaction_value = null) {
            if (ao_event === "" && transaction_value) {
                this.send(
                    'automacao_coleta_sequencial="' +
                        this.in_sequential_execute +
                        '"automacao_coleta_retorno="0"automacao_coleta_informacao="' +
                        transaction_value +
                        '"'
                );
            } else {
                this.send(
                    'automacao_coleta_sequencial="' +
                        this.in_sequential_execute +
                        '"automacao_coleta_retorno="0"automacao_coleta_informacao="' +
                        ao_event +
                        '"'
                );
            }
        },
        confirm: function (sequential) {
            let ls_transaction_type = "Cartao Vender";
            let ls_execute_tags =
                'servico="executar"retorno="0"sequencial="' + sequential + '"';

            ls_transaction_type = 'transacao="' + ls_transaction_type + '"';
            ls_execute_tags += ls_transaction_type;

            this.send(ls_execute_tags);
        },
        start: function () {
            this.send(
                'servico="iniciar"sequencial="' +
                    this.tags.increment_sequential() +
                    '"retorno="1"versao="1.0.0"aplicacao_tela="VBIAutomationTest"aplicacao="V$PagueClient"'
            );
        },
        finish: function () {
            this.send(
                'servico="finalizar"sequencial="' +
                    this.tags.increment_sequential() +
                    '"retorno="1"'
            );
        },
        init_debug_card: function () {
            const card_number = $("input.debug_tef_card_number").val();
            const card_expiring_date = $("input.debug_tef_expiring_date").val();
            const card_security_code = $("input.debug_tef_security_code").val();

            if (card_number && card_expiring_date && card_security_code) {
                this.debug_card = {
                    card_number: card_number,
                    card_expiring_date: card_expiring_date,
                    card_security_code: card_security_code,
                };
            } else {
                this.debug_card = false;
            }
        },
        start_operation: function (operation) {
            if (this.pos.debug) {
                this.init_debug_card();
            }

            if (!this.connect_init) {
                this.pos.gui.show_popup("error", {
                    title: "Cliente V$Pague não iniciado!",
                    body:
                        "Certifique-se de que o Cliente V$Pague está funcionando normalmente",
                });
            } else {
                this.operation = operation;
                this.start();
            }
        },
        send: function (as_buffer) {
            // Send the package.
            this.ws_connection.send(as_buffer);
            // Places the current transaction in the queue
            this.transaction_queue.push(as_buffer);
            this.trace("Send >>> " + as_buffer);
        },
    });

    return {
        TefProxy: TefProxy,
    };
});
