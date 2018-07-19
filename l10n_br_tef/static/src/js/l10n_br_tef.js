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

    var in_sequential = 2;
    var in_sequential_execute = 0;
    var io_connection = connect();
    var io_tags;
    var ls_transaction_global_value = '';
    var transaction_queue = new Array();
    var payment_type;
    var payment_name;
    var global_ls_product_type = "Credito-Banrisul";

    var card_number = "5162205574852131";
    var card_expiring_date = "12/20";
    var card_security_code = "078";

    var pinpad_connected = 0;

    function connect()
    {
        // Returns the established connection.
        return (new WebSocket('ws://localhost:60906'));
    }

    // Opens the connection and sends the first service
    io_connection.onopen = function()
    {
        // Reports that you are connected.
        trace('Connection successful');

        // Instantiate and initialize the tags for integration.
        io_tags = new tags();
        io_tags.initialize_tags();
    };

    /**
    Function for handling communication errors.
    */
    io_connection.onerror = function(error)
    {
        trace(error.data);
        //io_connection.close();
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
            if(check_completed_consult()) return;
            if(check_completed_execution()) return;

            // Credit without PinPad
            if(check_completed_start()) return;
            if(check_completed_start_execute()) return;
            if(check_completed_send_card_number()) return;
            if(check_completed_send_expiring_date()) return;
            if(check_completed_send_security_code()) return;
            if(check_authorized_operation()) return;

            // Credit with PinPad
            check_completed_send();
            if(check_inserted_card()) return;
            if(check_filled_value()) return;
            check_filled_value_send();
            if(check_inserted_password()) return;

            // Final checks
            if(check_approved_transaction()) return;
            if(check_removed_card()) return;
            if(finishes_operation()) return;
        }, 1000);
    };

    function check_completed_consult(){

        if((io_tags.servico == "consultar") && (io_tags.retorno == "0")) {

            return true;
        }
        else if((io_tags.servico == '')&& (io_tags.retorno != "0")) {
            redo_operation(io_tags.sequencial);
            return false;
        }
    }

    function check_completed_execution(){
        if((io_tags.automacao_coleta_palavra_chave === "transacao_cartao_numero") && (io_tags.automacao_coleta_tipo != "N")
            && (io_tags.automacao_coleta_retorno == "0")) {
            collect('');

            io_tags.automacao_coleta_palavra_chave = '';
            io_tags.automacao_coleta_tipo = '';
            io_tags.automacao_coleta_retorno = '';
            return true;
        }else{
            //Handle Exceptions Here
            return false;
        }
    }

    function check_completed_start(){
        if((io_tags.servico == "iniciar") && (io_tags.retorno == "1") && (io_tags.aplicacao_tela == "VBIAutomationTest")){
            execute();

            io_tags.aplicacao_tela = '';
            return true;
        } else {
            //Handle Exceptions Here
            return false;
        }
    }

    function check_completed_start_execute(){
        if((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_numero") && (io_tags.automacao_coleta_tipo == "N")
            && (io_tags.automacao_coleta_retorno == "0")){

            // Send the card number
            collect(card_number);

            io_tags.automacao_coleta_palavra_chave = '';
            io_tags.automacao_coleta_tipo = '';
            io_tags.automacao_coleta_retorno = '';
            return true;
        } else {
            //Handle Exceptions Here
            return false;
        }
    }

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

    function check_completed_send_security_code(){
        if((io_tags.automacao_coleta_palavra_chave == "transacao_valor") && (io_tags.automacao_coleta_tipo == "N")
            && (io_tags.automacao_coleta_retorno == "0")){
            for( var i=0; i < $('.paymentline-input').length; i++){
                if($('.paymentline-name')[i].innerText.indexOf(payment_name) != -1)
                ls_transaction_global_value = $(".paymentline-input")[i].value.replace(',','.');
            }
            // Send the value
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
    }

    function check_authorized_operation(){
        if(io_tags.automacao_coleta_mensagem === "Transacao autorizada"){
            collect('');

            io_tags.automacao_coleta_mensagem = '';
            return true;
        } else if(io_tags.mensagem === "Transacao autorizada") {

            confirm(io_tags.sequencial);
            io_tags.mensagem = '';
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
            ls_transaction_global_value = $('.paymentline-input')[1]['value'].replace(',', '.');

            collect('');

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

    function check_filled_value(){
        if(io_tags.automacao_coleta_mensagem == "AGUARDE A SENHA"){
            collect('');

            io_tags.automacao_coleta_mensagem = '';
            return true;
        } else {
          // Handle Exceptions Here
            return false;
        }
    }

    function check_filled_value_send(){
        // here the user must enter his password
    }

    function check_inserted_password(){
        if(io_tags.automacao_coleta_mensagem === "Aguarde !!! Processando a transacao ..."){
            collect('');

            io_tags.automacao_coleta_mensagem = "";
            return true;
        } else {
            // Handle Exceptions Here
            return false;
        }
    }

    function check_approved_transaction(){
        if((io_tags.automacao_coleta_mensagem === "Transacao aprovada.") &&
            (io_tags.servico == "") && (io_tags.transacao == "")) {
            collect('');

            io_tags.automacao_coleta_mensagem = '';
            return true;
        }else{
            // Handle Exceptions Here
            return false;
        }
    }

    function check_removed_card(){
        if((io_tags.servico == "executar") && (io_tags.mensagem == "Transacao aprovada., RETIRE O CARTAO")){
            confirm(io_tags.sequencial);

            io_tags.mensagem = "";
            return true;
        } else {
            // Handle Exceptions Here
            return false;
        }
    }

    function finishes_operation(){
        if((io_tags.retorno == "1") && (io_tags.servico == "executar") && (io_tags.transacao == "Cartao Vender") ){
            finish();

            io_tags.transacao = '';
            setTimeout(function(){
                consult();
            }, 2000);
            return true;
        } else {
            // Handle Exceptions Here
            return false;
        }
    }

    function trace(as_buffer) {
        console.log(as_buffer);
    }

    /**
    Necessary TAGs for integration.
    */
    function tags()
    {
        var aplicacao;
        var aplicacao_tela;
        var estado;
        var versao;
        var mensagem;
        var retorno;
        var sequencial;
        var servico;
        var transacao;
        var tipo_produto;
        var transacao_comprovante_1via;
        var automacao_coleta_palavra_chave;
        var automacao_coleta_tipo;
        var transacao_comprovante_2via;
        var transacao_comprovante_resumido;
        var transacao_informacao;
        var transacao_opcao;
        var transacao_pagamento;
        var transacao_parcela;
        var transacao_produto;
        var transacao_rede;
        var transacao_tipo_cartao;
        var transacao_administracao_usuario;
        var transacao_administracao_senha;
        var transacao_valor;
        var automacao_coleta_sequencial;
        var automacao_coleta_retorno;
        var automacao_coleta_mensagem;
        var automacao_coleta_informacao;
        var automacao_coleta_opcao;

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

    function execute()
    {

        var ls_execute_tags = 'servico="executar"retorno="1"sequencial="'+ sequential() +'"';

        var ls_card_type = (payment_type === "CD01")? "Debito" : "Credito";
        // var ls_card_type = "Credito";
        var ls_transaction_type = "Cartao Vender";
        var ls_product_type = global_ls_product_type;
        var ls_payment_transaction = "A vista";


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
    }

    function send(as_buffer)
    {
        // Send the package.
        io_connection.send(as_buffer);

        // Places the current transaction in the queue
        transaction_queue.push(as_buffer);
        trace("Send >>> " + as_buffer);
    }

    function start()
    {
        send('servico="iniciar"sequencial="'+ sequential() +'"retorno="1"versao="1.0.0"aplicacao_tela="VBIAutomationTest"aplicacao="V$PagueClient"');
    }

    function finish()
    {
        send('servico="finalizar"sequencial="'+sequential()+'"retorno="1"');
    }

    function consult()
    {
        send('servico="consultar"retorno="0"sequencial="'+ sequential()+'"');
    }

    function sequential()
    {
        // Incrementa o sequencial..
        in_sequential = (in_sequential+1);

        // document.getElementById('io_txt_sequencial').value = in_sequential;
        return(in_sequential);
    }

    function redo_operation(retorno_sequencial){
        if(transaction_queue.length > 0){
            setTimeout(function(){
                transaction_queue[transaction_queue.length-1] = transaction_queue[transaction_queue.length-1].replace(/sequencial="\d+"/, "sequencial=\"" + retorno_sequencial + "\"");
                    send(transaction_queue[transaction_queue.length-1]);
            }, 1000);
        }
    }

    function start_operation()
    {
        if (('consultar' === io_tags.servico)&& (io_tags.transacao_produto != '' )){
            if(payment_type === "CC01"){

                // With PinPad
                if(pinpad_connected){
                    execute()
                }
                // Without PinPad
                else{
                    global_ls_product_type = "Credito-Stone";
                    start();
                }

            }else if(payment_type === "CD01"){

            }

        }
    }

    module.Order = module.Order.extend({
        verificar_metodo_pagamento: function(){
            var payment_method = this.attributes.paymentLines.models;
        }
    });

    module.ProductScreenWidget.include({
        init: function(parent,options){
            this._super(parent,options);
            consult();
        }
    });

    module.PaymentScreenWidget.include({
        rerender_paymentline: function(line) {
            this._super(line);
        },
        render_paymentline: function(line){
            el_node = this._super(line);
            var self = this;
             
            if (["CD01", "CC01"].indexOf(line.cashregister.journal.code) > -1 &&
                this.pos.config.iface_tef){
                payment_type = line.cashregister.journal.code;
                payment_name = line.cashregister.journal.name;
                el_node.querySelector('.payment-terminal-transaction-start')
                    .addEventListener('click', function(){start_operation()});
            }
            return el_node;
        },
    });
};