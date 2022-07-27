/*
    l10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_br_tef.devices', function (require) {
    "use strict";

    let core = require('web.core');
    let ls_transaction_global_value = '';
    let ls_global_transaction_method = '';
    let ls_global_plots = 1;
    let ls_global_institution = '';
    let ls_global_environment = '';
    let transaction_queue = new Array();
    let payment_type;
    let payment_name;

    let ls_global_operation = '';

    let card_number;
    let card_expiring_date;
    let card_security_code;

    let cancellation_user = '';
    let cancellation_password = '';
    let cancellation_transaction_date = '';
    let cancellation_document_number = '';
    let cancellation_transaction_value = '';

    let connect_init = false;
    let set_interval_id = 0;

    let TefProxy = core.Class.extend({
        actions: [
            'product',
            'cashier',
            'client',
        ],
        init: function (attributes) {

            this.pos = attributes.pos;
            this.action_callback = {};
            this.ws_connection;
            this.in_sequential_execute = 0;
            this.tags = new this.tags();

            this.connect();
        },
        set_connected: function () {
            this.pos.set({'tef_status': {state: 'connected', pending: 0}});
        },
        set_connecting: function () {
            this.pos.set({'tef_status': {state: 'connected', pending: 0}});
        },
        set_warning: function () {
            this.pos.set({'tef_status': {state: 'warning', pending: 0}});
        },
        set_disconnected: function () {
            this.pos.set({'tef_status': {state: 'disconnected', pending: 0}});
        },
        set_error: function () {
            this.pos.set({'tef_status': {state: 'error', pending: 0}});
        },
        connect: function () {
            let self = this;
            // Returns the established connection.
            try {
                if ((this.ws_connection && this.ws_connection.readyState !== 1) || (this.ws_connection === undefined))
                    this.ws_connection = new WebSocket('ws://localhost:60906');

                if (this.ws_connection.readyState === 3)
                    return;

                // Opens the connection and sends the first service
                this.ws_connection.onopen = function () {
                    connect_init = true;
                    // Reports that you are connected.
                    self.set_connected();
                    self.trace('Connection successful');
                    // Initialize the tags for integration.
                    self.tags.initialize_tags();
                    self.consult();
                };

                /**
                 Function for handling connection closed.
                 */
                this.ws_connection.onclose = () => {
                    self.trace('Connection closed');
                    self.set_disconnected();
                    connect_init = false;
                    this.ws_connection.close();
                    self.abort();
                };

                /**
                 Function for handling communication errors.
                 */
                this.ws_connection.onerror = (error) => {
                    self.trace(error.data);
                    self.set_warning();
                    connect_init = false;
                    this.ws_connection.close();
                };

                /**
                 Function for receiving messages.
                 */
                this.ws_connection.onmessage = (e) => {
                    self.set_connecting();
                    // Shows the message.
                    self.trace("Received >>> " + e.data);

                    // Initializes Tags.
                    this.tags.initialize_tags();

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
                        /*
                         * TODO: Change the 'card_number' to a boolean to be checked if is with pinpad or not
                         *  Verify where to set this boolean
                         */
                        if (card_number) {
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
                console.log('Could not connect to server');
                this.set_error();
            }
        },

        check_withdrawal_amount: function () {
            if (this.tags.automacao_coleta_mensagem === "Valor do Saque") {
                this.collect('0');
                return true;
            }
            return false;
        },

        check_authorized_operation: function () {
            // Authorized operation -- Without PinPad
            if (this.tags.automacao_coleta_mensagem === "Transacao autorizada") {
                let transaction_value = this.pos.get('selectedOrder').selected_paymentline.amount;
                this.collect('', transaction_value);

                this.screenPopupPagamento('Transação Aprovada');

                this.tags.automacao_coleta_mensagem = '';
                return true;
            }
            // Authorized operation -- With PinPad
            else if (this.tags.mensagem === "Transacao autorizada") {

                this.screenPopupPagamento('Transação Aprovada');

                confirm(this.tags.sequencial);
                this.tags.mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_removed_card: function () {
            let self = this;
            if ((this.tags.servico == "executar") && (this.tags.mensagem && this.tags.mensagem === 'Transacao aprovada, RETIRE O CARTAO')) {
                self.confirm(this.tags.sequencial);

                setTimeout(function () {
                    self.screenPopupPagamento('Retire o Cartão');
                }, 1500);

                this.tags.mensagem = "";
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_approval_request: function () {
            if (this.tags.automacao_coleta_mensagem === "SOLICITANDO AUTORIZACAO, AGUARDE ...") {
                this.collect('');

                this.screenPopupPagamento('Solicitando Autorização');

                this.tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_chip_processing: function () {
            if (this.tags.automacao_coleta_mensagem === "Processando o cartao com CHIP") {
                this.collect('');

                this.screenPopupPagamento('Processando o cartao com CHIP... Por Favor, Insira a Senha.');

                this.tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_cancellation_ok: function () {
            if (this.tags.automacao_coleta_mensagem === ">CANCELAMENTO OK") {
                this.collect('');

                this.screenPopupPagamento('Cancelamento Autorizado!!!');

                this.tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_cancellation_remove_card: function () {
            let self = this;
            if (this.tags.mensagem === ">CANCELAMENTO OK, RETIRE O CARTAO") {
                confirm(this.tags.sequencial);

                setTimeout(function () {
                    self.screenPopupPagamento('Retire o Cartão');
                }, 1500);

                this.tags.mensagem = "";
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_cancellation_finishes: function () {
            let self = this;
            if ((this.tags.retorno == "1") && (this.tags.servico == "executar") && (this.tags.transacao == "Administracao Cancelar")) {
                self.finish();

                self.pos.gui.current_popup.hide();

                this.tags.transacao = '';
                setTimeout(function () {
                    self.consult();
                }, 2000);
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_inserted_password: function () {
            if (this.tags.automacao_coleta_mensagem === "Aguarde !!! Processando a transacao ...") {
                this.collect('');

                this.screenPopupPagamento('Processing the transaction...');

                this.tags.automacao_coleta_mensagem = "";
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_approved_transaction: function () {
            if ((this.tags.automacao_coleta_mensagem && this.tags.automacao_coleta_mensagem == "Transacao aprovada") &&
                (this.tags.servico == "") && (this.tags.transacao == "")) {

                this.screenPopupPagamento('Transaction Approved');
                this.collect('');

                this.tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_completed_start_execute: function () {
            /*
             * Message sequence to switch to manual card data input flow
             */
            if ((this.tags.automacao_coleta_palavra_chave === "transacao_cartao_numero")
                && (this.tags.automacao_coleta_retorno === "0") && (this.tags.automacao_coleta_mensagem === "INSIRA OU PASSE O CARTAO")) {

                this.send('automacao_coleta_sequencial="' + this.in_sequential_execute + '"automacao_coleta_retorno="0"');
                setTimeout(()=>{
                    this.send('automacao_coleta_sequencial="' + this.in_sequential_execute + '"automacao_coleta_retorno="9"');
                }, 1000)


                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_transaction_card_number: function () {
            /*
             * Confirm the option to manually enter card data
             */
            if ((this.tags.automacao_coleta_palavra_chave === "transacao_cartao_numero") && (this.tags.automacao_coleta_tipo === "X")
                && (this.tags.automacao_coleta_retorno === "0") && (this.tags.automacao_coleta_mensagem === "<SIM> CANCELAR, <NAO> LER")) {

                this.collect('Digitar');

                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_type_card_number: function () {
            /*
             * Send card number
             */
            if ((this.tags.automacao_coleta_palavra_chave === "transacao_cartao_numero") && (this.tags.automacao_coleta_tipo === "N")
                && (this.tags.automacao_coleta_retorno === "0") && (this.tags.automacao_coleta_mensagem === "Digite o numero do cartao")) {

                this.collect(card_number);

                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_completed_send_security_code: function () {
            if ((this.tags.automacao_coleta_palavra_chave == "transacao_valor") && (this.tags.automacao_coleta_tipo == "N")
                && (this.tags.automacao_coleta_retorno == "0")) {

                // Send the value
                let transaction_value;
                if (cancellation_transaction_value) {
                    transaction_value = cancellation_transaction_value;
                } else {
                    transaction_value = this.pos.get('selectedOrder').selected_paymentline.amount;
                }
                this.collect('', transaction_value);

                // Reset the Value
                ls_transaction_global_value = "";
                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                this.tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_completed_execution: function () {
            if ((this.tags.automacao_coleta_palavra_chave === "transacao_cartao_numero") && (this.tags.automacao_coleta_tipo != "N")
                && (this.tags.automacao_coleta_retorno == "0") && (!card_number)) {
                this.collect('');

                this.screenPopupPagamento('Please, insert the Card');

                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                this.tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },


        check_filled_value: function () {
            if (this.tags.automacao_coleta_mensagem == "AGUARDE A SENHA") {
                this.collect('');

                this.screenPopupPagamento('Please, enter the password');

                this.tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_request_confirmation: function () {
            if ((this.tags.automacao_coleta_mensagem && this.tags.automacao_coleta_mensagem.indexOf("Confirma o cancelamento desta transacao") > -1) && (this.tags.automacao_coleta_tipo === "X")) {

                this.pos.gui.show_popup('ConfirmaCancelamentoCompraPopup', {
                    'title': _t('Purchase Information'),
                    'body': _t(this.tags.automacao_coleta_mensagem),
                });

                this.tags.automacao_coleta_tipo = "";
                this.tags.automacao_coleta_mensagem = "";
                return true;

            } else {
                // Handle Exceptions Here
                return false;
            }

        },

        finishes_operation: function () {
            let self = this;
            if ((this.tags.retorno == "1") && (this.tags.servico == "executar") && (this.tags.transacao == "Cartao Vender")) {
                self.finish();
                self.complete_paymentline();

                self.pos.gui.current_popup.hide();

                this.tags.transacao = '';
                setTimeout(function () {
                    self.consult();
                }, 2000);
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        disable_order_transaction: function () {
            let payment_screen = this.pos.gui.current_screen;
            let order = this.pos.get_order();
            if (order) {
                order.tef_in_transaction = false;
                payment_screen.order_changes();
            }
        },

        complete_paymentline: function () {
            this.disable_order_transaction();
            let payment_screen = this.pos.gui.current_screen;
            let selected_paymentline = payment_screen.get_selected_paymentline();
            if (selected_paymentline) {
                selected_paymentline.tef_payment_completed = true;
                payment_screen.render_paymentlines()
            }
        },

        clearCancelamentoCompraPopup: function () {

            let modal_inputs = $(".modal-body input");
            let modal_inputs_length = modal_inputs.length;

            for (let i = 0; i < modal_inputs_length; i++) {
                modal_inputs[i].value = "";
            }
        },

        abort: function () {
            let self = this;

            if (self.pos.gui.current_popup) {
                self.pos.gui.current_popup.hide();
                self.clearCancelamentoCompraPopup();
                cancellation_user = "";
                cancellation_password = "";
                cancellation_document_number = "";
                cancellation_transaction_value = "";
            }
            setTimeout(function () {
                self.send('automacao_coleta_retorno="9"automacao_coleta_mensagem="Fluxo Abortado pelo operador!!"automacao_coleta_sequencial="' + (self.in_sequential_execute) + '"');
            }, 1000);

            setTimeout(function () {
                if (self.pos.gui.current_popup) {
                    self.pos.gui.current_popup.hide()
                }
            }, 3000);
        },

        redo_operation: function (sequential_return) {
            let self = this;
            if (transaction_queue.length > 0) {
                setTimeout(function () {
                    transaction_queue[transaction_queue.length - 1] = transaction_queue[transaction_queue.length - 1].replace(/sequencial="\d+"/, "sequencial=\"" + sequential_return + "\"");
                    self.send(transaction_queue[transaction_queue.length - 1]);
                }, 1000);
            }
        },

        check_completed_consult: function () {

            if ((this.tags.servico == "consultar") && (this.tags.retorno == "0")) {

                return true;
            } else if ((this.tags.automacao_coleta_mensagem != 'Fluxo Abortado pelo operador!!')
                && (this.tags.servico == '') && (this.tags.retorno != "0") && (!this.tags.mensagem)) {
                this.redo_operation(this.tags.sequencial);
                return false;
            } else {
                return false;
            }
        },

        check_cancelled_transaction: function () {
            if (this.tags.automacao_coleta_mensagem === 'Transacao cancelada') {
                this.disable_order_transaction();
                return true;
            } else {
                return false;
            }
        },

        screenPopupPagamento: function (msg) {
            console.log(msg);
            this.pos.gui.show_popup('StatusPagementoPopUp', {
                'title': _t('Please, wait!'),
                'body': _t(msg),
            });
        },

        check_completed_start: function () {
            if ((this.tags.servico == "iniciar") && (this.tags.retorno == "1") && (this.tags.aplicacao_tela == "VBIAutomationTest")) {

                let payment_term = $('.paymentline-input.payment_term').get('0');
                if (payment_term) {
                    ls_global_plots = payment_term.options[payment_term.selectedIndex].text.match(/\d+/)
                    if (ls_global_plots)
                        ls_global_plots = parseInt(ls_global_plots[0]);
                    else
                        ls_global_plots = 1;
                }

                if (!ls_global_institution && ls_global_plots > 1) {
                    this.pos.gui.show_popup('error', {
                        'title': 'No type of installment scheme selected!',
                        'body': 'You must select at least one institution in the POS settings',
                    });
                    return false;
                }
                this.execute();
                this.screenPopupPagamento('Initializing Operation');
                this.tags.aplicacao_tela = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_user_access: function () {
            if ((this.tags.automacao_coleta_mensagem === "Usuario de acesso") && (this.tags.automacao_coleta_tipo === "X") &&
                (this.tags.automacao_coleta_palavra_chave === "transacao_administracao_usuario")) {

                this.pos.gui.show_popup('CancelamentoCompraPopup', {});
                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        proceed_cancellation: function () {

            cancellation_user = $('.CancelamentoCompraPopup_usuario').val();
            cancellation_password = $('.CancelamentoCompraPopup_senha').val();
            cancellation_document_number = $('.CancelamentoCompraPopup_documento').val();
            cancellation_transaction_value = $('.CancelamentoCompraPopup_valor').val();

            let date = new Date($('.CancelamentoCompraPopup_data').val());
            if (date) {
                cancellation_transaction_date = (date.getDate() < 10 ? '0' + date.getDate() : date.getDate()) + '/' +
                    ((date.getMonth() + 1) < 10 ? '0' + (date.getMonth() + 1) : (date.getMonth() + 1)) + '/' +
                    date.getFullYear().toString().substring(2, 5)
            }

            let cancellation_info = 'transacao_tipo_cartao=""transacao_pagamento=""transacao_produto=""';
            this.send('automacao_coleta_sequencial="' + this.in_sequential_execute + '"automacao_coleta_retorno="0"automacao_coleta_informacao="' + cancellation_user + '"' + cancellation_info);

            this.clearCancelamentoCompraPopup();
        },

        confirm_proceed_cancellation: function (proceed) {

            let transaction_value = proceed ? "Sim" : "Nao";
            this.collect('', transaction_value);
        },

        check_user_password: function () {
            if ((this.tags.automacao_coleta_mensagem === "Senha de acesso") && (this.tags.automacao_coleta_tipo === "X") &&
                (this.tags.automacao_coleta_palavra_chave === "transacao_administracao_senha")) {

                this.collect('', cancellation_password);

                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;

            } else {
                return false;
            }
        },

        check_purchase_date: function () {
            if ((this.tags.automacao_coleta_mensagem === "Data Transacao Original") && (this.tags.automacao_coleta_tipo === "D") &&
                (this.tags.automacao_coleta_palavra_chave === "transacao_data")) {

                this.collect('', cancellation_transaction_date);

                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;

            } else {
                return false;
            }
        },

        check_document_number: function () {
            if ((this.tags.automacao_coleta_mensagem === "Numero do Documento") && (this.tags.automacao_coleta_tipo === "N") &&
                (this.tags.automacao_coleta_palavra_chave === "transacao_nsu")) {

                this.collect('', cancellation_document_number);

                this.tags.automacao_coleta_mensagem = "";
                this.tags.automacao_coleta_palavra_chave = "";
                this.tags.automacao_coleta_tipo = "";
                return true;

            } else {
                return false;
            }
        },

        check_payment_method: function () {
            if ((this.tags.automacao_coleta_mensagem === "Forma de Pagamento") && (this.tags.automacao_coleta_palavra_chave === "transacao_pagamento")
                && (this.tags.automacao_coleta_tipo === "X")) {

                this.collect(ls_global_transaction_method);
                this.screenPopupPagamento('Payment ' + ls_global_transaction_method);
                this.tags.automacao_coleta_mensagem = '';
                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_institution: function () {
            if ((this.tags.automacao_coleta_mensagem === "Financiado pelo") && (this.tags.automacao_coleta_palavra_chave === "transacao_financiado")
                && (this.tags.automacao_coleta_tipo === "X")) {
                this.collect(ls_global_institution);
                this.tags.automacao_coleta_mensagem = '';
                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_plots: function () {
            if ((this.tags.automacao_coleta_mensagem === "Parcelas") && (this.tags.automacao_coleta_palavra_chave === "transacao_parcela")
                && (this.tags.automacao_coleta_tipo === "N")) {
                this.collect(ls_global_plots);
                this.screenPopupPagamento('Payment in ' + ls_global_plots + ' installments');
                this.tags.automacao_coleta_mensagem = '';
                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_for_errors: function () {
            // Here all the exceptions will be handle

            // For any other exceptions, just abort the operation
            if ((this.tags.automacao_coleta_retorno === "9" && this.tags.automacao_coleta_mensagem === "Fluxo Abortado pelo operador!!" && this.tags.retorno != "2")) {
                return true;
            } else if (this.tags.automacao_coleta_mensagem === "Digite o numero do cartao") {
                this.screenPopupPagamento('Erro - PinPad não conectado!!!');
                this.abort();
            } else if (this.tags.automacao_coleta_mensagem === "TRANSACAO ORIGINAL NAO LOCALIZADA") {
                this.screenPopupPagamento('Erro - Transação Original não Localizada!!!');
                this.abort();
            } else if (this.tags.automacao_coleta_mensagem === "Problema na conexao") {
                this.screenPopupPagamento('Erro - Problema na Conexão!!!');
                this.abort();
            } else if ((this.tags.automacao_coleta_mensagem || false) && (this.tags.automacao_coleta_mensagem.startsWith("Transacao cancelada"))) {
                this.tags.automacao_coleta_mensagem = '';
                return true;
            } else if (this.tags.automacao_coleta_mensagem === "INSIRA OU PASSE O CARTAO") {
                return true;
            } else if (this.tags.automacao_coleta_mensagem === "RETIRE O CARTAO") {
                this.screenPopupPagamento('Operação Cancelada - Retire o Cartão!!!');
                return true;
            } else if (this.tags.servico === "finalizar") {
                return true;
            } else if (this.tags.servico === "iniciar") {
                return true;
            } else if (this.tags.mensagem && this.tags.mensagem.startsWith("Sequencial invalido")) {
                this.tags.mensagem = '';
                this.redo_operation(this.tags.sequencial);
                return true;
            } else {
                let message = this.tags.message || this.tags.automacao_coleta_mensagem;
                if (message)
                    this.screenPopupPagamento(message);
                this.abort();
            }
        },

        execute: function () {

            let ls_execute_tags = 'servico="executar"retorno="1"sequencial="' + this.tags.increment_sequential() + '"';
            let ls_payment_transaction = '';
            let ls_card_type = '';
            let ls_product_type = '';
            let ls_transaction_type = '';

            let debit_server = this.pos.config.debit_server;
            let credit_server = this.pos.config.credit_server;

            let selected_payment_line = this.pos.gui.current_screen.get_selected_paymentline();

            if (ls_global_operation === "purchase") {
                ls_transaction_type = "Cartao Vender";

                let payment_type = selected_payment_line.cashregister.journal.tef_payment_mode;

                if (payment_type === "01") {
                    ls_card_type = "Credito";
                } else if (payment_type === "02") {
                    ls_card_type = "Debito";
                } else {
                    ls_card_type = "";
                }

                if (ls_global_environment === "Homologacao")
                    ls_product_type = (payment_type === "CD01") ? debit_server : credit_server;
                if (ls_global_environment === "Producao")
                    ls_product_type = "MASTERCARD";

            } else if (ls_global_operation === "cancellation") {
                ls_transaction_type = "Administracao Cancelar";
            }

            if (ls_global_plots > 1) {
                if (ls_global_institution === "Administradora")
                    ls_global_transaction_method = "2-Financ.Adm."
                else if (ls_global_institution === "Estabelecimento")
                    ls_global_transaction_method = "3-Financ.Loja"
            } else {
                ls_global_transaction_method = "A vista"
            }

            if (ls_transaction_global_value !== "") {
                ls_transaction_global_value = 'transacao_valor="' + ls_transaction_global_value + '"';
                ls_execute_tags = ls_execute_tags + ls_transaction_global_value;
            }


            if (ls_transaction_type != "") {
                ls_transaction_type = 'transacao="' + ls_transaction_type + '"';
                ls_execute_tags = ls_execute_tags + ls_transaction_type;
            }

            if (ls_card_type != "") {
                ls_card_type = 'transacao_tipo_cartao="' + ls_card_type + '"';
                ls_execute_tags = ls_execute_tags + ls_card_type;

            }

            if (ls_payment_transaction != "") {
                ls_payment_transaction = 'transacao_pagamento="' + ls_payment_transaction + '"';
                ls_execute_tags = ls_execute_tags + ls_payment_transaction;
            }

            if (ls_product_type != "") {
                ls_product_type = 'transacao_produto="' + ls_product_type + '"';
                ls_execute_tags = ls_execute_tags + ls_product_type;
            }

            this.send(ls_execute_tags);
        },

        consult: function () {
            this.send('servico="consultar"retorno="0"sequencial="' + this.tags.increment_sequential() + '"');

            setTimeout(function () {
                if (self.posmodel.gui.current_popup) {
                    self.posmodel.gui.current_popup.hide()
                }
            }, 1000);
        },

        check_completed_send_card_number: function () {
            if ((this.tags.automacao_coleta_palavra_chave == "transacao_cartao_validade") && (this.tags.automacao_coleta_tipo == "D")
                && (this.tags.automacao_coleta_retorno == "0")) {

                // Send the card expiring date
                this.collect(card_expiring_date);

                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                this.tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        check_completed_send_expiring_date: function () {
            if ((this.tags.automacao_coleta_palavra_chave == "transacao_cartao_codigo_seguranca") && (this.tags.automacao_coleta_tipo == "X")
                && (this.tags.automacao_coleta_retorno == "0")) {

                // Send the card security code
                this.collect(card_security_code);

                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                this.tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        check_completed_send: function () {
            if (this.tags.automacao_coleta_retorno == "0") {
                // Here the user must insert the card

                this.tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        check_inserted_card: function () {
            if ((this.tags.automacao_coleta_palavra_chave === "transacao_valor") && (this.tags.automacao_coleta_tipo != "N")) {
                // Transaction Value
                let transaction_value = this.pos.get('selectedOrder').selected_paymentline.amount

                this.collect('', transaction_value);

                this.screenPopupPagamento('Starting Operation');

                // Reset the Value
                ls_transaction_global_value = "";
                this.tags.automacao_coleta_palavra_chave = '';
                this.tags.automacao_coleta_tipo = '';
                this.tags.automacao_coleta_retorno = '';
                return true;
            } else {
                return false;
            }
        },
        check_filled_value_send: function () {
            // here the user must enter his password
        },
        trace: function (as_buffer) {
            console.log(as_buffer);
        },

        /**
         Necessary TAGs for integration.
         */
        tags: function () {
            this.fill_tags = function (as_tag, as_value) {
                if ('automacao_coleta_opcao' === as_tag)
                    this.automacao_coleta_opcao = as_value;

                else if ('automacao_coleta_informacao' === as_tag)
                    this.automacao_coleta_informacao = as_value;

                else if ('automacao_coleta_mensagem' === as_tag)
                    this.automacao_coleta_mensagem = as_value;

                else if ('automacao_coleta_retorno' === as_tag)
                    this.automacao_coleta_retorno = as_value;

                else if ('automacao_coleta_sequencial' === as_tag)
                    this.automacao_coleta_sequencial = as_value;

                else if ('transacao_comprovante_1via' === as_tag)
                    this.transacao_comprovante_1via = as_value;

                else if ('transacao_comprovante_2via' === as_tag)
                    this.transacao_comprovante_2via = as_value;

                else if ('transacao_comprovante_resumido' === as_tag)
                    this.transacao_comprovante_resumido = as_value;

                else if ('servico' === as_tag)
                    this.servico = as_value;

                else if ('transacao' === as_tag)
                    this.transacao = as_value;

                else if ('transacao_produto' === as_tag)
                    this.transacao_produto = as_value;

                else if ('retorno' === as_tag)
                    this.retorno = as_value;

                else if ('mensagem' === as_tag)
                    this.mensagem = as_value;

                else if ('sequencial' === as_tag)
                    this.sequencial = parseInt(as_value, 0);

                else if ('automacao_coleta_palavra_chave' === as_tag)
                    this.automacao_coleta_palavra_chave = as_value;

                else if ('automacao_coleta_tipo' === as_tag)
                    this.automacao_coleta_tipo = as_value;

                else if ('estado' === as_tag)
                    this.estado = as_value;

                else if ('aplicacao_tela' === as_tag)
                    this.aplicacao_tela = as_value;
            };

            this.initialize_tags = function () {
                this.transacao_comprovante_1via = '';
                this.transacao_comprovante_2via = '';
                this.transacao = '';
                this.transacao_produto = '';
                this.servico = '';
                this.retorno = 0;
                this.sequencial = 0;
            };

            this.increment_sequential = function () {
              this.sequencial = this.sequencial + 1
              return this.sequencial
            };
        },
        disassembling_service: function (to_service) {

            let ln_start = 0;
            let ln_end = to_service.toString().indexOf("\n\r\n\t\t\r\n\t\t\t\r\n\t\t\r\n\t");
            let ls_tag = "";
            let ls_value = "";

            try {
                // While reading the received packet isn't finished ...
                while (ln_start < ln_end) {

                    // Recovers the TAG..
                    ls_tag = to_service.toString().substring(ln_start, to_service.indexOf('="', ln_start));
                    ln_start = ln_start + (ls_tag.toString().length) + 2;

                    ls_value = to_service.toString().substring(
                        ln_start, (ln_start = to_service.toString().indexOf('\"\n', ln_start)));

                    ln_start += 2;

                    this.tags.fill_tags(ls_tag, ls_value);
                }
            } catch (err) {
                alert('Internal Error: ' + err.message);
            }
        },
        collect: function (ao_event, transaction_value=null) {
            if (ao_event === '' && transaction_value) {
                this.send('automacao_coleta_sequencial="' + this.in_sequential_execute + '"automacao_coleta_retorno="0"automacao_coleta_informacao="' + transaction_value + '"');
            } else {
                this.send('automacao_coleta_sequencial="' + this.in_sequential_execute + '"automacao_coleta_retorno="0"automacao_coleta_informacao="' + ao_event + '"');
            }
        },
        confirm: function (sequential) {
            let ls_transaction_type = "Cartao Vender";
            let ls_execute_tags = 'servico="executar"retorno="0"sequencial="' + sequential + '"';

            ls_transaction_type = 'transacao="' + ls_transaction_type + '"';
            ls_execute_tags = ls_execute_tags + ls_transaction_type;

            this.send(ls_execute_tags);
        },
        start: function () {
            this.send('servico="iniciar"sequencial="' + this.tags.increment_sequential() + '"retorno="1"versao="1.0.0"aplicacao_tela="VBIAutomationTest"aplicacao="V$PagueClient"');
        },
        finish: function () {
            this.send('servico="finalizar"sequencial="' + this.tags.increment_sequential() + '"retorno="1"');
        },
        start_operation: function (operation) {
            // FIXME: Deixar isso ativo somente no modo debug;
            card_number = $('input.debug_tef_card_number').val();
            card_expiring_date = $('input.debug_tef_expiring_date').val();
            card_security_code = $('input.debug_tef_security_code').val();

            if (!connect_init) {
                this.pos.gui.show_popup('error', {
                    'title': 'Cliente V$Pague não iniciado!',
                    'body': 'Certifique-se de que o Cliente V$Pague está funcionando normalmente',
                });
            } else {
                ls_global_operation = operation;
                this.start();
            }
        },
        send: function (as_buffer) {
            // Send the package.
            this.ws_connection.send(as_buffer);
            // Places the current transaction in the queue
            transaction_queue.push(as_buffer);
            this.trace("Send >>> " + as_buffer);
        }
    });

    return {
        TefProxy: TefProxy,
    };
});
