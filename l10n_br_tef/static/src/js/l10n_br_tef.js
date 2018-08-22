/******************************************************************************
 *    L10N_BR_TEF
 *    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
 *    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
 *    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
 *    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 ******************************************************************************/

openerp.l10n_br_tef = function(instance){

    module = instance.point_of_sale;
    var _t = instance.web._t;

    var in_sequential = 2;
    var in_sequential_execute = 0;
    var io_tags;
    var ls_transaction_global_value = '';
    var ls_global_transaction_method = '';
    var ls_global_plots = 1;
    var ls_global_institution = '';
    var transaction_queue = new Array();
    var payment_type;
    var payment_name;

    var dev_mode = false;

    var card_number = "5442556260904012";
    var card_expiring_date = "03/19";
    var card_security_code = "624";

    var connect_init = false;
    var set_interval_id = 0;

    module.PindPadWidget = module.StatusWidget.extend({
        template: 'PinPadStatusWidget',

        start: function(){
            this.$el.click(function(){
                connect();
            });
        },
    });

    module.StatusPagementoPopUp = module.PopUpWidget.extend({
        template: 'StatusPagamentoPopUp',
        hotkeys_handlers: {},

        show: function(options){
            var self = this;
            this._super();
            this.message = options.message || '';
            this.comment = options.comment || '';
            this.renderElement();
        },
    });

    module.PosOrderListWidget = module.PosBaseWidget.extend({
        template: 'PosOrderListWidget',
        renderElement: function() {
            var self = this;
            this._super();

            var button = new module.PosOrderListButtonWidget(self,{
                pos: self.pos,
                pos_widget : self.pos_widget,
            });
            button.appendTo(self.$el);
        }
    });

    module.PosWidget = module.PosWidget.extend({
        build_widgets: function(){
            this._super();
            this.close_button = new module.HeaderButtonWidget(this,{
                label: _t('Close'),
                action: function(){
                    var self = this;
                    if (!this.confirmed) {
                        this.$el.addClass('confirm');
                        this.$el.text(_t('Confirm'));
                        this.confirmed = setTimeout(function(){
                            self.$el.removeClass('confirm');
                            self.$el.text(_t('Close'));
                            self.confirmed = false;
                        },2000);
                    } else {
                        clearTimeout(this.confirmed);
                        clearInterval(set_interval_id);
                        this.pos_widget.close();
                    }
                },
            });
            this.pind_pad_button = new module.PindPadWidget(this,{});
            this.pind_pad_button.appendTo(this.$('.pos-rightheader'));
            $('.header-button').remove();
            this.close_button.appendTo(this.$('.pos-rightheader'));

            this.popupStatusPagamento = new module.StatusPagementoPopUp(this,{});
            this.popupStatusPagamento.appendTo(this.$('.screens'));
            this.popupStatusPagamento.hide();
            this.screen_selector.popup_set['popupStatusPagamento'] = this.popupStatusPagamento;


         },
    });

    function check_completed_send_card_number(){
        if((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_validade") && (io_tags.automacao_coleta_tipo == "D")
            && (io_tags.automacao_coleta_retorno == "0")){

            // Send the card expiring date
            collect(card_expiring_date);

            io_tags.automacao_coleta_palavra_chave = '';
            io_tags.automacao_coleta_tipo = '';
            io_tags.automacao_coleta_retorno = '';
            return true;
        } else {
            //Handle Exceptions Here
            return false;
        }
    }

    function check_completed_send_expiring_date(){
        if((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_codigo_seguranca") && (io_tags.automacao_coleta_tipo == "X")
            && (io_tags.automacao_coleta_retorno == "0")){

            // Send the card security code
            collect(card_security_code);

            io_tags.automacao_coleta_palavra_chave = '';
            io_tags.automacao_coleta_tipo = '';
            io_tags.automacao_coleta_retorno = '';
            return true;
        } else {
            //Handle Exceptions Here
            return false;
        }
    }

    function check_completed_send(){
        if(io_tags.automacao_coleta_retorno == "0"){
            // Here the user must insert the card

            io_tags.automacao_coleta_retorno = '';
            return true;
        } else {
            //Handle Exceptions Here
            return false;
        }
    }

    function check_inserted_card(){
        if((io_tags.automacao_coleta_palavra_chave === "transacao_valor") && (io_tags.automacao_coleta_tipo != "N")){
            // Transaction Value
            ls_transaction_global_value = this.pos.get('selectedOrder').selected_paymentline.amount

            collect('');

            this.screenPopupPagamento('Iniciando a Operação');

            // Reset the Value
            ls_transaction_global_value = "";
            io_tags.automacao_coleta_palavra_chave = '';
            io_tags.automacao_coleta_tipo = '';
            io_tags.automacao_coleta_retorno = '';
            return true;
        } else {
            return false;
        }
    }

    function check_filled_value_send(){
        // here the user must enter his password
    }

    function trace(as_buffer) {
        console.log(as_buffer);
    }

    /**
    Necessary TAGs for integration.
    */
    function tags()
    {
        this.fill_tags = function(as_tag, as_value)
        {
            if('automacao_coleta_opcao' === as_tag)
                this.automacao_coleta_opcao = as_value;

            else if ('automacao_coleta_informacao' === as_tag )
                this.automacao_coleta_informacao = as_value;

            else if ('automacao_coleta_mensagem' === as_tag)
                this.automacao_coleta_mensagem = as_value;

            else if ('automacao_coleta_retorno' === as_tag )
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
                this.sequencial = parseInt(as_value,0);

            else if ('automacao_coleta_palavra_chave' === as_tag)
                this.automacao_coleta_palavra_chave = as_value;

            else if ('automacao_coleta_tipo' === as_tag)
                this.automacao_coleta_tipo = as_value;

            else if ('estado' === as_tag)
                this.estado = as_value;

            else if ('aplicacao_tela' === as_tag)
                this.aplicacao_tela = as_value;
        };

        this.initialize_tags = function()
        {
            this.transacao_comprovante_1via = '';
            this.transacao_comprovante_2via = '';
            this.transacao = '';
            this.transacao_produto = '';
            this.servico = '';
            this.retorno = 0;
            this.sequencial = 0;
        };
    }

    function disassembling_service(to_service) {

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
        }
        catch (err) {
            alert('Internal Error: ' + err.message);
        }
    }

    function collect(ao_event)
    {
        if(ao_event == '') {
            send('automacao_coleta_sequencial="'+in_sequential_execute+'"automacao_coleta_retorno="0"automacao_coleta_informacao="'+ ls_transaction_global_value + '"');
        } else{
            send('automacao_coleta_sequencial="'+in_sequential_execute+'"automacao_coleta_retorno="0"automacao_coleta_informacao="'+ ao_event + '"');
        }
    }

    function confirm(sequential)
    {
        var ls_transaction_type = "Cartao Vender";
        var ls_execute_tags = 'servico="executar"retorno="0"sequencial="'+ sequential + '"';

        ls_transaction_type = 'transacao="' + ls_transaction_type+'"';
        ls_execute_tags = ls_execute_tags + ls_transaction_type;

        send(ls_execute_tags);
    }

    function start()
    {
        send('servico="iniciar"sequencial="'+ sequential() +'"retorno="1"versao="1.0.0"aplicacao_tela="VBIAutomationTest"aplicacao="V$PagueClient"');
    }

    function finish()
    {
        send('servico="finalizar"sequencial="'+sequential()+'"retorno="1"');
    }

    function sequential()
    {
        // Increments the senquential..
        in_sequential = (in_sequential+1);

        // document.getElementById('io_txt_sequencial').value = in_sequential;
        return(in_sequential);
    }

    function start_operation()
    {
        // abort();
        start();
    }

    module.ProductScreenWidget.include({
        init: function(parent,options){
            var self = this;
            this._super(parent,options);
            this.connect();
            set_interval_id =
                setInterval(function(){
                if (!connect_init)
                    self.connect();
            }, 10000);
        },

        connect: function()
        {
            var self = this;
            // Returns the established connection.
            try {
                io_connection = new WebSocket('ws://localhost:60906');

                // Opens the connection and sends the first service
                    io_connection.onopen = function()
                {
                    connect_init = true;
                    // Reports that you are connected.
                    $(".connected").removeClass("oe_hidden");
                    $(".disconnected").addClass("oe_hidden");
                    trace('Connection successful');
                    // Instantiate and initialize the tags for integration.
                    io_tags = new tags();
                    io_tags.initialize_tags();
                    self.consult();
                };

             /**
               Function for handling connection closed.
                */
                io_connection.onclose = function () {
                    trace('Connection closed');
                    $(".connected").addClass("oe_hidden");
                    $(".disconnected").removeClass("oe_hidden");
                    connect_init = false;
                    io_connection.close();
                    self.abort();
                };

                /**
                Function for handling communication errors.
                */
                io_connection.onerror = function(error)
                {
                    trace(error.data);
                    $(".connected").addClass("oe_hidden");
                    $(".disconnected").removeClass("oe_hidden");
                    connect_init = false;
                    io_connection.close();
                };

                /**
                Function for receiving messages.
                */
                io_connection.onmessage = function(e){

                    // Shows the message.
                    trace("Received >>> " + e.data);

                    // Initializes Tags.
                    io_tags.initialize_tags();

                    // Show the received Tags.
                    disassembling_service(e.data);

                    // If 'retorno' isn't OK
                    if( io_tags.retorno !== "0" ) {
                        in_sequential = io_tags.sequencial;
                    }

                    // Saves the current sequence of the collection.
                    in_sequential_execute = io_tags.automacao_coleta_sequencial;
                    setTimeout(function(){
                        // Initial Checks
                        if(self.check_completed_consult()) return;
                        if(self.check_completed_execution()) return;
                        if(self.check_completed_start()) return;

                        // Credit without PinPad
                        // Only works if dev_mode is true
                        if(dev_mode){
                            if(self.check_completed_start_execute()) return;
                            if(check_completed_send_card_number()) return;
                            if(check_completed_send_expiring_date()) return;
                        }

                        if(self.check_completed_send_security_code()) return;
                        if(self.check_authorized_operation()) return;

                        // Credit with PinPad
                        // check_completed_send();
                        if(check_inserted_card()) return;
                        if(self.check_filled_value()) return;
                        check_filled_value_send();

                        if(self.check_payment_method()) return;
                        if(self.check_institution()) return;
                        if(self.check_plots()) return;

                        if(self.check_inserted_password()) return;

                        // Final checks
                        if(self.check_approved_transaction()) return;
                        if(self.check_removed_card()) return;
                        if(self.finishes_operation()) return;
                        if(self.check_for_errors()) return;
                    }, 1000);
                };
            }
            catch (err){
                console.log('Nao foi possivel estalecer uma conexao com o servidor')
            }
        },

        check_authorized_operation: function(){
            // Authorized operation -- Without PinPad
            if(io_tags.automacao_coleta_mensagem === "Transacao autorizada"){
                collect('');

                this.screenPopupPagamento('Transação Aprovada');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            }
            // Authorized operation -- With PinPad
            else if(io_tags.mensagem === "Transacao autorizada") {

                this.screenPopupPagamento('Transação Aprovada');

                confirm(io_tags.sequencial);
                io_tags.mensagem = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_removed_card: function(){
            var self = this;
            if((io_tags.servico == "executar") && (io_tags.mensagem && io_tags.mensagem.indexOf("APROVADA, RETIRE O CARTAO") > -1)){
                confirm(io_tags.sequencial);

                setTimeout(function(){
                    self.screenPopupPagamento('Retire o Cartão');
                }, 1500);

                io_tags.mensagem = "";
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_inserted_password: function(){
            if(io_tags.automacao_coleta_mensagem === "Aguarde !!! Processando a transacao ..."){
                collect('');

                this.screenPopupPagamento('Processando a transação ...');

                io_tags.automacao_coleta_mensagem = "";
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        check_approved_transaction: function(){
            if((io_tags.automacao_coleta_mensagem && io_tags.automacao_coleta_mensagem.indexOf("APROVADA") > -1) &&
                (io_tags.servico == "") && (io_tags.transacao == "")) {

                this.screenPopupPagamento('Transação Aprovada');
                collect('');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            }else{
                // Handle Exceptions Here
                return false;
            }
        },

        check_completed_start_execute: function(){
            if((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_numero") && (io_tags.automacao_coleta_tipo == "N")
                && (io_tags.automacao_coleta_retorno == "0")){

                // Send the card number
                collect(card_number);

                this.screenPopupPagamento('Por favor, insira a senha');

                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_completed_send_security_code: function(){
            if((io_tags.automacao_coleta_palavra_chave == "transacao_valor") && (io_tags.automacao_coleta_tipo == "N")
                && (io_tags.automacao_coleta_retorno == "0")){

                // Send the value
                ls_transaction_global_value = this.pos.get('selectedOrder').selected_paymentline.amount
                collect('');

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

        check_completed_execution: function()
        {
            if((io_tags.automacao_coleta_palavra_chave === "transacao_cartao_numero") && (io_tags.automacao_coleta_tipo != "N")
                && (io_tags.automacao_coleta_retorno == "0")) {
                collect('');

                this.screenPopupPagamento('Por favor, insira ou passe o Cartão');

                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                io_tags.automacao_coleta_retorno = '';
                return true;
            }else{
                //Handle Exceptions Here
                return false;
            }
        },


        check_filled_value: function(){
            if(io_tags.automacao_coleta_mensagem == "AGUARDE A SENHA"){
                collect('');

                this.screenPopupPagamento('Por favor, insira a senha');

                io_tags.automacao_coleta_mensagem = '';
                return true;
            } else {
              // Handle Exceptions Here
                return false;
            }
        },

        finishes_operation: function(){
            var self = this;
            if((io_tags.retorno == "1") && (io_tags.servico == "executar") && (io_tags.transacao == "Cartao Vender") ){
                finish();

                self.pos_widget.popupStatusPagamento.hide()

                io_tags.transacao = '';
                setTimeout(function(){
                    self.consult();
                }, 2000);
                return true;
            } else {
                // Handle Exceptions Here
                return false;
            }
        },

        abort: function()
        {
            var self = this;
            setTimeout(function(){
                    send('automacao_coleta_retorno="9"automacao_coleta_mensagem="Fluxo Abortado pelo operador!!"sequencial="'+(in_sequential_execute)+'"');
            }, 1000);

            setTimeout(function(){
                if (self.pos_widget){
                    self.pos_widget.popupStatusPagamento.hide()
                }
            }, 3000);
        },

        redo_operation: function(sequential_return)
        {
            var self = this;
            if(transaction_queue.length > 0){
                setTimeout(function(){
                    transaction_queue[transaction_queue.length-1] = transaction_queue[transaction_queue.length-1].replace(/sequencial="\d+"/, "sequencial=\"" + sequential_return + "\"");
                        send(transaction_queue[transaction_queue.length-1]);
                }, 1000);
            }
        },

        check_completed_consult: function()
        {

            if((io_tags.servico == "consultar") && (io_tags.retorno == "0")) {

                return true;
            }
            else if((io_tags.automacao_coleta_mensagem != 'Fluxo Abortado pelo operador!!' ) && (io_tags.servico == '')&& (io_tags.retorno != "0")) {
                this.redo_operation(io_tags.sequencial);
                return false;
            } else {
                return false;
            }
        },

        screenPopupPagamento: function (msg) {
            this.pos_widget.screen_selector.show_popup('popupStatusPagamento', {
                            message: _t('Por Favor Aguarde!'),
                            comment: _t(msg),
                            });
        },

        check_completed_start: function(){
            if((io_tags.servico == "iniciar") && (io_tags.retorno == "1") && (io_tags.aplicacao_tela == "VBIAutomationTest")){

                var payment_term = $('.paymentline-input.payment_term').get('0');
                if(payment_term){
                    ls_global_plots = payment_term.options[payment_term.selectedIndex].text.match(/\d+/)
                    if(ls_global_plots)
                        ls_global_plots = parseInt(ls_global_plots[0]);
                    else
                        ls_global_plots = 1
                }

                if(!ls_global_institution && ls_global_plots > 1){
                    this.pos.pos_widget.screen_selector.show_popup('error',{
                        message: 'Nenhuma modalidade de parcelamento selecionada!',
                        comment: 'Você precisa selecionar pelo menos uma instituição nas configurações do POS',
                    });
                    return false;
                }
                this.execute();
                this.screenPopupPagamento('Iniciando a Operação');
                io_tags.aplicacao_tela = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_payment_method: function(){
            if((io_tags.automacao_coleta_mensagem === "Forma de Pagamento") && (io_tags.automacao_coleta_palavra_chave === "transacao_pagamento")
                && (io_tags.automacao_coleta_tipo === "X")){

                collect(ls_global_transaction_method);
                this.screenPopupPagamento('Pagamento ' + ls_global_transaction_method);
                io_tags.automacao_coleta_mensagem = '';
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },
        
        check_institution: function(){
            if((io_tags.automacao_coleta_mensagem === "Financiado pelo") && (io_tags.automacao_coleta_palavra_chave === "transacao_financiado")
                && (io_tags.automacao_coleta_tipo === "X")){
                collect(ls_global_institution);
                io_tags.automacao_coleta_mensagem = '';
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_plots: function(){
            if((io_tags.automacao_coleta_mensagem === "Parcelas") && (io_tags.automacao_coleta_palavra_chave === "transacao_parcela")
                && (io_tags.automacao_coleta_tipo === "N")){
                collect(ls_global_plots);
                this.screenPopupPagamento('Pagamento em ' + ls_global_plots + ' vezes');
                io_tags.automacao_coleta_mensagem = '';
                io_tags.automacao_coleta_palavra_chave = '';
                io_tags.automacao_coleta_tipo = '';
                return true;
            } else {
                //Handle Exceptions Here
                return false;
            }
        },

        check_for_errors: function(){
            // Here all the exceptions will be handle

            // For any other exceptions, just abort the operation
            if((io_tags.automacao_coleta_retorno === "9" && io_tags.automacao_coleta_mensagem === "Fluxo Abortado pelo operador!!")){
                return true;
            }else if(io_tags.automacao_coleta_mensagem === "Digite o numero do cartao"){
                this.screenPopupPagamento('Erro - PinPad não conectado!!!');
                this.abort();
            }else if(io_tags.automacao_coleta_mensagem === "Problema na conexao"){
                this.screenPopupPagamento('Erro - Problema na Conexão!!!');
                this.abort();
            }else if((io_tags.automacao_coleta_mensagem || false) && (io_tags.automacao_coleta_mensagem.startsWith("Transacao cancelada"))) {
                io_tags.automacao_coleta_mensagem = '';
                return true;
            }else if(io_tags.automacao_coleta_mensagem === "INSIRA OU PASSE O CARTAO"){
                return true;
            }else if(io_tags.servico === "finalizar"){
                return true;
            }else if(io_tags.servico === "iniciar"){
                return true;
            }else if(io_tags.mensagem && io_tags.mensagem.startsWith("Sequencial invalido") && !io_tags.automacao_coleta_mensagem){
                return true;
            }else{
                var message = io_tags.message || io_tags.automacao_coleta_mensagem;
                if(message)
                    this.screenPopupPagamento(message);
                this.abort();
            }
        },

        execute: function()
        {

            var ls_execute_tags = 'servico="executar"retorno="1"sequencial="'+ sequential() +'"';
            var ls_payment_transaction = '';
            var ls_card_type = '';
            var ls_product_type = (payment_type === "CD01")? "Debito-Getnetlac" : "Credito-Getnetlac";
            var ls_transaction_type = "Cartao Vender";

            ls_global_transaction_method = (ls_global_plots > 1)? "Parcelado": "A vista";


             if (ls_transaction_global_value !== "") {
                 ls_transaction_global_value = 'transacao_valor="'+ls_transaction_global_value+'"';
                 ls_execute_tags = ls_execute_tags+ls_transaction_global_value;
             }


             if (ls_transaction_type != "") {
                 ls_transaction_type = 'transacao="'+ls_transaction_type+'"';
                 ls_execute_tags = ls_execute_tags+ls_transaction_type;
             }

             if (ls_card_type != "") {
                 ls_card_type  = 'transacao_tipo_cartao="'+ls_card_type+'"';
                 ls_execute_tags = ls_execute_tags+ls_card_type;

             }

             if ( ls_payment_transaction != "") {
                 ls_payment_transaction = 'transacao_pagamento="'+ls_payment_transaction+'"';
                 ls_execute_tags = ls_execute_tags+ls_payment_transaction;
             }

             if ( ls_product_type != "" ){
                 ls_product_type = 'transacao_produto="'+ls_product_type+'"';
                 ls_execute_tags = ls_execute_tags+ls_product_type;
             }

             send(ls_execute_tags);
        },

        consult: function()
        {
            send('servico="consultar"retorno="0"sequencial="'+ sequential()+'"');

            setTimeout(function(){
                if (self.pos_widget){
                    self.pos_widget.popupStatusPagamento.hide()
                }
            }, 1000);
        },
    });

    function send(as_buffer)
    {
        // Send the package.
        io_connection.send(as_buffer);
        // Places the current transaction in the queue
        transaction_queue.push(as_buffer);
        trace("Send >>> " + as_buffer);
    };

    module.PaymentScreenWidget.include({
        rerender_paymentline: function(line) {
            this._super(line);
        },
        render_paymentline: function(line){
            el_node = this._super(line);
            var self = this;

            if (["CD01", "CC01"].indexOf(line.cashregister.journal.code) > -1 &&
                this.pos.config.iface_tef){
                ls_global_institution = this.pos.config.institution_selection;

                payment_type = line.cashregister.journal.code;
                payment_name = line.cashregister.journal.name;
                el_node.querySelector('.payment-terminal-transaction-start')
                    .addEventListener('click', function(){
                        start_operation();
                    });
            }
            return el_node;
        },
    });
};