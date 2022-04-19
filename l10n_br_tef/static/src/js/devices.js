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

    var core = require('web.core');
    var io_connection;
    var in_sequential = 2;
    var in_sequential_execute = 0;
    var io_tags;
    var ls_transaction_global_value = '';
    var ls_global_transaction_method = '';
    var ls_global_plots = 1;
    var ls_global_institution = '';
    var ls_global_environment = '';
    var transaction_queue = new Array();
    var payment_type;
    var payment_name;

    var ls_global_operation = '';

    var card_number;
    var card_expiring_date;
    var card_security_code;

    var cancellation_user = '';
    var cancellation_password = '';
    var cancellation_transaction_date = '';
    var cancellation_document_number = '';
    var cancellation_transaction_value = '';

    var connect_init = false;
    var set_interval_id = 0;

    var TefProxy = core.Class.extend({
        actions: [
            'product',
            'cashier',
            'client',
        ],
        init: function (attributes) {
            this.pos = attributes.pos;
            this.action_callback = {};
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
            var self = this;
            // Returns the established connection.
            try {
                if ((io_connection && io_connection.readyState !== 1) || (io_connection === undefined))
                    io_connection = new WebSocket('ws://localhost:60906');

                if (io_connection.readyState === 3)
                    return;

                // Opens the connection and sends the first service
                io_connection.onopen = function () {
                    connect_init = true;
                    // Reports that you are connected.
                    self.set_connected();
                    self.trace('Connection successful');
                    // Instantiate and initialize the tags for integration.
                    io_tags = new self.tags();
                    io_tags.initialize_tags();
                    self.consult();
                };

                /**
                 Function for handling connection closed.
                 */
                io_connection.onclose = function () {
                    self.trace('Connection closed');
                    self.set_disconnected();
                    connect_init = false;
                    io_connection.close();
                    self.abort();
                };

                /**
                 Function for handling communication errors.
                 */
                io_connection.onerror = function (error) {
                    self.trace(error.data);
                    self.set_warning();
                    connect_init = false;
                    io_connection.close();
                };

                /**
                 Function for receiving messages.
                 */
                io_connection.onmessage = function (e) {
                    self.set_connecting();
                    // Shows the message.
                    self.trace("Received >>> " + e.data);

                    // Initializes Tags.
                    io_tags.initialize_tags();

                    // Show the received Tags.
                    self.disassembling_service(e.data);

                    // If 'retorno' isn't OK
                    if (io_tags.retorno !== "0") {
                        in_sequential = io_tags.sequencial;
                    }

                    // Saves the current sequence of the collection.
                    in_sequential_execute = io_tags.automacao_coleta_sequencial;
                    setTimeout(function () {
                        // Initial Checks
                        if (self.check_completed_consult()) return;
                        if (self.check_completed_execution()) return;
                        if (self.check_completed_start()) return;

                        // Cancellation Operations
                        if (self.check_user_access()) return;
                        if (self.check_user_password()) return;
                        if (self.check_purchase_date()) return;
                        if (self.check_document_number()) return;

                        // Credit without PinPad
                        // Only works if card_number is filled in Debug mode
                        if (card_number) {
                            if (self.check_completed_start_execute()) return;
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
            if (io_tags.automacao_coleta_mensagem === "Valor do Saque") {
                this.collect('0');
                return true;
            }
            return false;
        },

        check_authorized_operation: function () {
            // Authorized operation -- Without PinPad
            if (io_tags.automacao_coleta_mensagem === "Transacao autorizada") {
                this.collect('');

                this.screenPopupPagamento('Transação Aprovada');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            }
            // Authorized operation -- With PinPad
            else if (io_tags.mensagem === "Transacao autorizada") {

                this.screenPopupPagamento('Transação Aprovada');

                confirm(io_tags.sequencial);
                io_tags.mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_removed_card: function () {
            var self = this;
            if ((io_tags.servico == "executar") && (io_tags.mensagem && io_tags.mensagem === 'Transacao aprovada, RETIRE O CARTAO')) {
                self.confirm(io_tags.sequencial);

                setTimeout(function () {
                    self.screenPopupPagamento('Retire o Cartão');
                }, 1500);

                io_tags.mensagem = "";
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_approval_request: function () {
            if (io_tags.automacao_coleta_mensagem === "SOLICITANDO AUTORIZACAO, AGUARDE ...") {
                this.collect('');

                this.screenPopupPagamento('Solicitando Autorização');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_chip_processing: function () {
            if (io_tags.automacao_coleta_mensagem === "Processando o cartao com CHIP") {
                this.collect('');

                this.screenPopupPagamento('Processando o cartao com CHIP... Por Favor, Insira a Senha.');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_cancellation_ok: function () {
            if (io_tags.automacao_coleta_mensagem === ">CANCELAMENTO OK") {
                this.collect('');

                this.screenPopupPagamento('Cancelamento Autorizado!!!');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_cancellation_remove_card: function () {
            var self = this;
            if (io_tags.mensagem === ">CANCELAMENTO OK, RETIRE O CARTAO") {
                confirm(io_tags.sequencial);

                setTimeout(function () {
                    self.screenPopupPagamento('Retire o Cartão');
                }, 1500);

                io_tags.mensagem = "";
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_cancellation_finishes: function () {
            var self = this;
            if ((io_tags.retorno == "1") && (io_tags.servico == "executar") && (io_tags.transacao == "Administracao Cancelar")) {
                self.finish();

                self.pos.gui.current_popup.hide();

                io_tags.transacao = '';
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
            if (io_tags.automacao_coleta_mensagem === "Aguarde !!! Processando a transacao ...") {
                this.collect('');

                this.screenPopupPagamento('Processing the transaction...');

                io_tags.automacao_coleta_mensagem = "";
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_approved_transaction: function () {
            if ((io_tags.automacao_coleta_mensagem && io_tags.automacao_coleta_mensagem == "Transacao aprovada") &&
                (io_tags.servico == "") && (io_tags.transacao == "")) {

                this.screenPopupPagamento('Transaction Approved');
                this.collect('');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_completed_start_execute: function () {
            if ((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_numero") && (io_tags.automacao_coleta_tipo == "N")
                && (io_tags.automacao_coleta_retorno == "0")) {

                // Send the card number
                this.collect(card_number);

                this.screenPopupPagamento('Please, enter the password');

                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_completed_send_security_code: function () {
            if ((io_tags.automacao_coleta_palavra_chave == "transacao_valor") && (io_tags.automacao_coleta_tipo == "N")
                && (io_tags.automacao_coleta_retorno == "0")) {

                // Send the value
                if (cancellation_transaction_value) {
                    ls_transaction_global_value = cancellation_transaction_value;
                } else {
                    ls_transaction_global_value = this.pos.get('selectedOrder').selected_paymentline.amount;
                }
                this.collect('');

                // Reset the Value
                ls_transaction_global_value = "";
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_completed_execution: function () {
            if ((io_tags.automacao_coleta_palavra_chave === "transacao_cartao_numero") && (io_tags.automacao_coleta_tipo != "N")
                && (io_tags.automacao_coleta_retorno == "0")) {
                this.collect('');

                this.screenPopupPagamento('Please, insert the Card');

                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },


        check_filled_value: function () {
            if (io_tags.automacao_coleta_mensagem == "AGUARDE A SENHA") {
                this.collect('');

                this.screenPopupPagamento('Please, enter the password');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_request_confirmation: function () {
            if ((io_tags.automacao_coleta_mensagem && io_tags.automacao_coleta_mensagem.indexOf("Confirma o cancelamento desta transacao") > -1) && (io_tags.automacao_coleta_tipo === "X")) {

                this.pos.gui.show_popup('ConfirmaCancelamentoCompraPopup', {
                    'title': _t('Purchase Information'),
                    'body': _t(io_tags.automacao_coleta_mensagem),
                });

                io_tags.automacao_coleta_tipo = "";
                io_tags.automacao_coleta_mensagem = "";
                return true;

            } else {
                // Handle Exceptions Here
                return false;
            }

        },

        finishes_operation: function () {
            var self = this;
            if ((io_tags.retorno == "1") && (io_tags.servico == "executar") && (io_tags.transacao == "Cartao Vender")) {
                self.finish();
                self.complete_paymentline();

                self.pos.gui.current_popup.hide();

                io_tags.transacao = '';
                setTimeout(function () {
                    self.consult();
                }, 2000);
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        complete_paymentline: function () {
            let payment_screen = this.pos.gui.current_screen;
            let order = this.pos.get_order();
            if (order) {
                order.tef_in_transaction = false;
                payment_screen.order_changes();
            }

            let selected_paymentline = payment_screen.get_selected_paymentline();
            if (selected_paymentline) {
                selected_paymentline.tef_payment_completed = true;
                payment_screen.render_paymentlines()
            }
        },

        clearCancelamentoCompraPopup: function () {

            var modal_inputs = $(".modal-body input");
            var modal_inputs_length = modal_inputs.length;

            for (var i = 0; i < modal_inputs_length; i++) {
                modal_inputs[i].value = "";
            }
        },

        abort: function () {
            var self = this;

            if (self.pos.gui.current_popup) {
                self.pos.gui.current_popup.hide();
                self.clearCancelamentoCompraPopup();
                cancellation_user = "";
                cancellation_password = "";
                cancellation_document_number = "";
                cancellation_transaction_value = "";
            }
            setTimeout(function () {
                self.send('automacao_coleta_retorno="9"automacao_coleta_mensagem="Fluxo Abortado pelo operador!!"sequencial="' + (in_sequential_execute) + '"');
            }, 1000);

            setTimeout(function () {
                if (self.pos.gui.current_popup) {
                    self.pos.gui.current_popup.hide()
                }
            }, 3000);
        },

        redo_operation: function (sequential_return) {
            var self = this;
            if (transaction_queue.length > 0) {
                setTimeout(function () {
                    transaction_queue[transaction_queue.length - 1] = transaction_queue[transaction_queue.length - 1].replace(/sequencial="\d+"/, "sequencial=\"" + sequential_return + "\"");
                    self.send(transaction_queue[transaction_queue.length - 1]);
                }, 1000);
            }
        },

        check_completed_consult: function () {

            if ((io_tags.servico == "consultar") && (io_tags.retorno == "0")) {

                return true;
            } else if ((io_tags.automacao_coleta_mensagem != 'Fluxo Abortado pelo operador!!')
                && (io_tags.servico == '') && (io_tags.retorno != "0") && (!io_tags.mensagem)) {
                this.redo_operation(io_tags.sequencial);
                return false;
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
            if ((io_tags.servico == "iniciar") && (io_tags.retorno == "1") && (io_tags.aplicacao_tela == "VBIAutomationTest")) {

                var payment_term = $('.paymentline-input.payment_term').get('0');
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
                io_tags.aplicacao_tela = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_user_access: function () {
            if ((io_tags.automacao_coleta_mensagem === "Usuario de acesso") && (io_tags.automacao_coleta_tipo === "X") &&
                (io_tags.automacao_coleta_palavra_chave === "transacao_administracao_usuario")) {

                this.pos.gui.show_popup('CancelamentoCompraPopup', {});
                io_tags.automacao_coleta_mensagem = "";
                io_tags.automacao_coleta_palavra_chave = "";
                io_tags.automacao_coleta_tipo = "";
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

            var date = new Date($('.CancelamentoCompraPopup_data').val());
            if (date) {
                cancellation_transaction_date = (date.getDate() < 10 ? '0' + date.getDate() : date.getDate()) + '/' +
                    ((date.getMonth() + 1) < 10 ? '0' + (date.getMonth() + 1) : (date.getMonth() + 1)) + '/' +
                    date.getFullYear().toString().substring(2, 5)
            }

            ls_transaction_global_value = cancellation_user;

            var cancellation_info = 'transacao_tipo_cartao=""transacao_pagamento=""transacao_produto=""';
            this.send('automacao_coleta_sequencial="' + in_sequential_execute + '"automacao_coleta_retorno="0"automacao_coleta_informacao="' + ls_transaction_global_value + '"' + cancellation_info);

            this.clearCancelamentoCompraPopup();
        },

        confirm_proceed_cancellation: function (proceed) {

            ls_transaction_global_value = proceed ? "Sim" : "Nao";
            this.collect('');

            ls_transaction_global_value = "";
        },

        check_user_password: function () {
            if ((io_tags.automacao_coleta_mensagem === "Senha de acesso") && (io_tags.automacao_coleta_tipo === "X") &&
                (io_tags.automacao_coleta_palavra_chave === "transacao_administracao_senha")) {

                ls_transaction_global_value = cancellation_password;
                this.collect('');

                io_tags.automacao_coleta_mensagem = "";
                io_tags.automacao_coleta_palavra_chave = "";
                io_tags.automacao_coleta_tipo = "";
                return true;

            } else {
                return false;
            }
        },

        check_purchase_date: function () {
            if ((io_tags.automacao_coleta_mensagem === "Data Transacao Original") && (io_tags.automacao_coleta_tipo === "D") &&
                (io_tags.automacao_coleta_palavra_chave === "transacao_data")) {

                ls_transaction_global_value = cancellation_transaction_date;
                this.collect('');

                io_tags.automacao_coleta_mensagem = "";
                io_tags.automacao_coleta_palavra_chave = "";
                io_tags.automacao_coleta_tipo = "";
                return true;

            } else {
                return false;
            }
        },

        check_document_number: function () {
            if ((io_tags.automacao_coleta_mensagem === "Numero do Documento") && (io_tags.automacao_coleta_tipo === "N") &&
                (io_tags.automacao_coleta_palavra_chave === "transacao_nsu")) {

                ls_transaction_global_value = cancellation_document_number;
                this.collect('');

                io_tags.automacao_coleta_mensagem = "";
                io_tags.automacao_coleta_palavra_chave = "";
                io_tags.automacao_coleta_tipo = "";
                return true;

            } else {
                return false;
            }
        },

        check_payment_method: function () {
            if ((io_tags.automacao_coleta_mensagem === "Forma de Pagamento") && (io_tags.automacao_coleta_palavra_chave === "transacao_pagamento")
                && (io_tags.automacao_coleta_tipo === "X")) {

                this.collect(ls_global_transaction_method);
                this.screenPopupPagamento('Payment ' + ls_global_transaction_method);
                io_tags.automacao_coleta_mensagem = '';
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_institution: function () {
            if ((io_tags.automacao_coleta_mensagem === "Financiado pelo") && (io_tags.automacao_coleta_palavra_chave === "transacao_financiado")
                && (io_tags.automacao_coleta_tipo === "X")) {
                this.collect(ls_global_institution);
                io_tags.automacao_coleta_mensagem = '';
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_plots: function () {
            if ((io_tags.automacao_coleta_mensagem === "Parcelas") && (io_tags.automacao_coleta_palavra_chave === "transacao_parcela")
                && (io_tags.automacao_coleta_tipo === "N")) {
                this.collect(ls_global_plots);
                this.screenPopupPagamento('Payment in ' + ls_global_plots + ' installments');
                io_tags.automacao_coleta_mensagem = '';
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_for_errors: function () {
            // Here all the exceptions will be handle

            // For any other exceptions, just abort the operation
            if ((io_tags.automacao_coleta_retorno === "9" && io_tags.automacao_coleta_mensagem === "Fluxo Abortado pelo operador!!" && io_tags.retorno != "2")) {
                return true;
            } else if (io_tags.automacao_coleta_mensagem === "Digite o numero do cartao") {
                this.screenPopupPagamento('Erro - PinPad não conectado!!!');
                this.abort();
            } else if (io_tags.automacao_coleta_mensagem === "TRANSACAO ORIGINAL NAO LOCALIZADA") {
                this.screenPopupPagamento('Erro - Transação Original não Localizada!!!');
                this.abort();
            } else if (io_tags.automacao_coleta_mensagem === "Problema na conexao") {
                this.screenPopupPagamento('Erro - Problema na Conexão!!!');
                this.abort();
            } else if ((io_tags.automacao_coleta_mensagem || false) && (io_tags.automacao_coleta_mensagem.startsWith("Transacao cancelada"))) {
                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else if (io_tags.automacao_coleta_mensagem === "INSIRA OU PASSE O CARTAO") {
                return true;
            } else if (io_tags.automacao_coleta_mensagem === "RETIRE O CARTAO") {
                this.screenPopupPagamento('Operação Cancelada - Retire o Cartão!!!');
                return true;
            } else if (io_tags.servico === "finalizar") {
                return true;
            } else if (io_tags.servico === "iniciar") {
                return true;
            } else if (io_tags.mensagem && io_tags.mensagem.startsWith("Sequencial invalido")) {
                io_tags.mensagem = '';
                this.redo_operation(io_tags.sequencial);
                return true;
            } else {
                var message = io_tags.message || io_tags.automacao_coleta_mensagem;
                if (message)
                    this.screenPopupPagamento(message);
                this.abort();
            }
        },

        execute: function () {

            var ls_execute_tags = 'servico="executar"retorno="1"sequencial="' + this.sequential() + '"';
            var ls_payment_transaction = '';
            var ls_card_type = '';
            var ls_product_type = '';
            var ls_transaction_type = '';

            var debit_server = this.pos.config.debit_server;
            var credit_server = this.pos.config.credit_server;

            let selected_payment_line = this.pos.gui.current_screen.get_selected_paymentline();

            if (ls_global_operation === "purchase") {
                var ls_transaction_type = "Cartao Vender";

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
                var ls_transaction_type = "Administracao Cancelar";
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
            this.send('servico="consultar"retorno="0"sequencial="' + this.sequential() + '"');

            setTimeout(function () {
                if (self.posmodel.gui.current_popup) {
                    self.posmodel.gui.current_popup.hide()
                }
            }, 1000);
        },

        check_completed_send_card_number: function () {
            if ((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_validade") && (io_tags.automacao_coleta_tipo == "D")
                && (io_tags.automacao_coleta_retorno == "0")) {

                // Send the card expiring date
                this.collect(card_expiring_date);

                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        check_completed_send_expiring_date: function () {
            if ((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_codigo_seguranca") && (io_tags.automacao_coleta_tipo == "X")
                && (io_tags.automacao_coleta_retorno == "0")) {

                // Send the card security code
                this.collect(card_security_code);

                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        check_completed_send: function () {
            if (io_tags.automacao_coleta_retorno == "0") {
                // Here the user must insert the card

                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        check_inserted_card: function () {
            if ((io_tags.automacao_coleta_palavra_chave === "transacao_valor") && (io_tags.automacao_coleta_tipo != "N")) {
                // Transaction Value
                ls_transaction_global_value = this.pos.get('selectedOrder').selected_paymentline.amount

                this.collect('');

                this.screenPopupPagamento('Starting Operation');

                // Reset the Value
                ls_transaction_global_value = "";
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
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
        },
        disassembling_service: function (to_service) {

            var ln_start = 0;
            var ln_end = to_service.toString().indexOf("\n\r\n\t\t\r\n\t\t\t\r\n\t\t\r\n\t");
            var ls_tag = "";
            var ls_value = "";

            try {
                // While reading the received packet isn't finished ...
                while (ln_start < ln_end) {

                    // Recovers the TAG..
                    ls_tag = to_service.toString().substring(ln_start, to_service.indexOf('="', ln_start));
                    ln_start = ln_start + (ls_tag.toString().length) + 2;

                    ls_value = to_service.toString().substring(
                        ln_start, (ln_start = to_service.toString().indexOf('\"\n', ln_start)));

                    ln_start += 2;

                    io_tags.fill_tags(ls_tag, ls_value);
                }
            } catch (err) {
                alert('Internal Error: ' + err.message);
            }
        },
        collect: function (ao_event) {
            if (ao_event == '') {
                this.send('automacao_coleta_sequencial="' + in_sequential_execute + '"automacao_coleta_retorno="0"automacao_coleta_informacao="' + ls_transaction_global_value + '"');
            } else {
                this.send('automacao_coleta_sequencial="' + in_sequential_execute + '"automacao_coleta_retorno="0"automacao_coleta_informacao="' + ao_event + '"');
            }
        },
        confirm: function (sequential) {
            var ls_transaction_type = "Cartao Vender";
            var ls_execute_tags = 'servico="executar"retorno="0"sequencial="' + sequential + '"';

            ls_transaction_type = 'transacao="' + ls_transaction_type + '"';
            ls_execute_tags = ls_execute_tags + ls_transaction_type;

            this.send(ls_execute_tags);
        },
        start: function () {
            this.send('servico="iniciar"sequencial="' + this.sequential() + '"retorno="1"versao="1.0.0"aplicacao_tela="VBIAutomationTest"aplicacao="V$PagueClient"');
        },
        finish: function () {
            this.send('servico="finalizar"sequencial="' + this.sequential() + '"retorno="1"');
        },
        sequential: function () {
            // Increments the senquential..
            in_sequential = (in_sequential + 1);

            // document.getElementById('io_txt_sequencial').value = in_sequential;
            return (in_sequential);
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
            io_connection.send(as_buffer);
            // Places the current transaction in the queue
            transaction_queue.push(as_buffer);
            this.trace("Send >>> " + as_buffer);
        }
    });

    return {
        TefProxy: TefProxy,
    };
});
