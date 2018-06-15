/******************************************************************************
 *    L10N_BR_TEF
 *    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
 *    @author Luis Felipe Miléo <mileo@kmee.com.br>
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

    // var ln_font_size = 4;

    var in_sequencial = 2;

    var in_sequencial_executar = 0;

    var io_connection = Conectar();

    var io_tags;

    var ls_transacao_valor_global = '';

    var fila_transacoes = new Array();

    function Conectar()
    {
        // Retorna a conexão estabelecida.
        return	(new WebSocket('ws://localhost:60906'));
    }

    // Abre a conexão e envia o primeiro servico.
    io_connection.onopen = function()
    {
        // Informa que conectou com sucesso.
        Trace('Connection successful');

        // Instancia as tag's para integração.
        io_tags	= new Tags();

        // Inicializa as tag's.
        io_tags.TagsInicializar();
    }

    /**
    Função para tratamento dos erros na comunicação.
    */
    io_connection.onerror = function(error)
    {
        Trace(error.data);
        //io_connection.close();
    }

    /**
    Função para troca de mensagem.
    */
    io_connection.onmessage	= function(e)
    {
        // Apresenta a mensagem.
        Trace("Received >>> " + e.data);

        // Inicia as tag's.
        io_tags.TagsInicializar();

        // Mosta as tag's recebidas.
        ServicoDesmontar(e.data);

        // Se retorno não for de pacote ok...
        if	( io_tags.retorno !== "0" )
        {
            in_sequencial = io_tags.sequencial;

        }

        // Guarda o sequencial corrente da coleta.
        in_sequencial_executar = io_tags.automacao_coleta_sequencial;

        setTimeout(function(){
            verifica_consultar_completo();
            verifica_executar_completo();
            verifica_executar_enviar_completo();
            verifica_cartao_inserido();
            verifica_valor_preenchido();
            verifica_valor_preenchido_enviar();
            verifica_senha_inserida();
            verifica_transacao_aprovada();
            verifica_cartao_removido();
            finaliza_operacao();
        }, 1000);


        // Apresenta o comprovante..
        // if	( io_tags.transacao_comprovante_1via !== '')
        // {
        //     alert(io_tags.transacao_comprovante_1via+io_tags.transacao_comprovante_2via);
        // }
    }

    function verifica_consultar_completo(){

        if((io_tags.servico == "consultar") && (io_tags.retorno == "0")) {
            Executar();
        }
        else if((io_tags.servico == '')&& (io_tags.retorno != "0")) {
            refaz_transacao(io_tags.sequencial);
        }
    }

    function verifica_executar_completo(){
        if((io_tags.automacao_coleta_palavra_chave == "transacao_cartao_numero") && (io_tags.automacao_coleta_retorno == "0")) {
            Coleta('');
        }else{
            //Tratar excessões
        }
    }

    function verifica_executar_enviar_completo(){

        if(io_tags.automacao_coleta_retorno == "0"){
            // Aqui o usuário\funcionário deverá inserir o cartão no PinPad
        } else {
            //Tratar Excessões
        }
    }

    function verifica_cartao_inserido(){
            if((io_tags.automacao_coleta_palavra_chave === "transacao_valor") && (io_tags.automacao_coleta_mensagem === "Valor" )){

                /* Aqui deverão ser preenchidos os valores
                    --> Pagamento
                    --> Produto
                    --> Tipo de Transação
                    --> Tipo Cartão
                */
                ls_transacao_valor_global = "1";


                Coleta('');
            }
    }

    function verifica_valor_preenchido(){
        if(io_tags.automacao_coleta_mensagem == "AGUARDE A SENHA"){

            ls_transacao_valor_global = '';
            Coleta('');

        } else {
          // Tratar Excessões
        }
    }

    function verifica_valor_preenchido_enviar(){
        // Aqui o usuário deverá preencher sua senha no PinPad
    }

    function verifica_senha_inserida(){
        if(io_tags.automacao_coleta_mensagem === "Aguarde !!! Processando a transacao ..."){
            Coleta('');
        } else {
            // Tratar Excessões
        }
    }

    function verifica_transacao_aprovada(){
        if((io_tags.automacao_coleta_mensagem === "Transacao aprovada.") && (io_tags.servico == "") && (io_tags.transacao == "")) {
            Coleta('');
        }else{
            // Tratar Excessões
        }
    }

    function verifica_cartao_removido(){

        if((io_tags.servico=="executar") && (io_tags.mensagem=="Transacao aprovada., RETIRE O CARTAO")){

            Confirmar(io_tags.sequencial);
            io_tags.mensagem = ""

        } else {
            // Tratar Excessões
        }
    }

    function finaliza_operacao(){
        if((io_tags.retorno=="1") && (io_tags.servico=="executar") && (io_tags.transacao=="Cartao Vender") ){
            Finalizar();
        } else {
            // Tratar Excessões
        }
    }

    // Função para visualização dos pacotes trocados.
    function Trace(as_buffer)
    {
        console.log(as_buffer);
    }

    //
    //
    // function Iniciar()
    // {
    //     Send('servico="iniciar"sequencial="'+Sequencial()+'"retorno="1"versao="1.0.0"aplicacao_tela="VBIAutomationTest"aplicacao="V$PagueClient"');
    // }
    //
    //
    // /**
    // Função responsável por montar e enviar o serviço "executar".
    // */
    //
    // function Limpar()
    // {
    //     document.getElementById('output').innerHTML
    //                     =		'';
    //     /**
    //     io_lst_transacao_tipo.selectedIndex
    //                     =		0;
    //     io_lst_tipo_cartao.selectedIndex
    //                     =		0;
    //     io_lst_transacao_pagamento.selectedIndex
    //                     =		0;
    //     */
    //
    // }
    //
    // function SequencialAdicionar()
    // {
    //     in_sequencial			=		in_sequencial++;
    //     document.getElementById('io_txt_sequencial').value
    //                     =	in_sequencial;
    //     return(in_sequencial);
    // }
    //
    //
    // function CartaoDigitar()
    // {
    //     Send('automacao_coleta_retorno="9"automacao_coleta_sequencial="'+(in_sequencial_executar)+'"');
    // }
    //
    // function FluxoAbortar()
    // {
    //     Send('automacao_coleta_retorno="9"automacao_coleta_mensagem="Fluxo Abortado pelo operador!!"sequencial="'+(in_sequencial_executar)+'"');
    // }
    //
    // function Mostrar(ao_event)
    // {
    //     var
    //     ls_tipo_servico	=	document.getElementById('io_lst_tipo_servico_mostrar').options[io_lst_tipo_servico_mostrar.selectedIndex].text;
    //
    //     if	(
    //             ls_tipo_servico		===	''
    //         )
    //     {
    //         ls_tipo_servico		=		document.getElementById('io_txt_servico_mostrar').text;
    //     }
    //
    //     if	(
    //             (ao_event		===	'')
    //             ||
    //             (ao_event.keyCode	===	13)
    //         )
    //     {
    //         Send('servico="mostrar"retorno="1"sequencial="'+Sequencial()+'"mensagem="'+ls_tipo_servico+'"');
    //     }
    // }
    //
    // function Coletar()
    // {
    //     var
    //     ls_tipo_servico	=	document.getElementById('io_lst_tipo_servico_coletar').options[io_lst_tipo_servico_coletar.selectedIndex].text;
    //
    //     Send('servico="coletar"retorno="1"sequencial="'+Sequencial()+'"mensagem="'+ls_tipo_servico+'"');
    // }
    //
    // function Perguntar()
    // {
    //     var
    //     ls_tipo_servico	=	document.getElementById('io_lst_tipo_servico_perguntar').options[io_lst_tipo_servico_perguntar.selectedIndex].text;
    //
    //     Send('servico="perguntar"retorno="1"sequencial="'+Sequencial()+'"mensagem="'+ls_tipo_servico+'+'+document.getElementById('io_txt_coleta_informacao').value+'"');
    // }
    //
    // //
    // // Função para envio dos dados.
    // //


    /**
    Tags nessessárias para a integração.
    */
    function Tags()
    {
        var
        aplicacao;

        var
        aplicacao_tela;

        var
        estado;

        var
        versao;

        var
        mensagem;

        var
        retorno;

        var
        sequencial;

        var
        servico;

        var
        transacao;

        var
        tipo_produto;

        var
        transacao_comprovante_1via;

        var
        automacao_coleta_palavra_chave;

        var
        transacao_comprovante_2via;

        var
        transacao_comprovante_resumido;

        var
        transacao_informacao;

        var
        transacao_opcao;

        var
        transacao_pagamento;

        var
        transacao_parcela;

        var
        transacao_produto;

        var
        transacao_rede;

        var
        transacao_tipo_cartao;

        var
        transacao_administracao_usuario;

        var
        transacao_administracao_senha;

        var
        transacao_valor;


        var
        automacao_coleta_sequencial;

        var
        automacao_coleta_retorno;

        var
        automacao_coleta_mensagem;

        var
        automacao_coleta_informacao;

        var
        automacao_coleta_opcao;


        this.TagsAlimentar = function(as_tag, as_value)
        {
            //Trace('Alimentando...'+as_tag);

            //this.automacao_coleta_opcao = "";
            //this.automacao_coleta_informacao = "";
            //this.automacao_coleta_mensagem = "";
            //this.automacao_coleta_retorno = "";
            //this.automacao_coleta_sequencial = "";
            //this.transacao_comprovante_1via = "";
            //this.transacao_comprovante_2via = "";
            //this.transacao_comprovante_resumido = "";
            //this.servico = "";
            //this.transacao = "";
            //this.transacao_produto = "";
            //this.retorno = 0;
            //this.sequencial = 0;
            //this.automacao_coleta_palavra_chave = "";


            if('automacao_coleta_opcao' === as_tag)
                this.automacao_coleta_opcao	= as_value;

            else if	('automacao_coleta_informacao'	===	as_tag )
                this.automacao_coleta_informacao = as_value;

            else if	('automacao_coleta_mensagem' === as_tag)
                this.automacao_coleta_mensagem = as_value;

            else if	('automacao_coleta_retorno'	===	as_tag )
                this.automacao_coleta_retorno = as_value;

            else if	('automacao_coleta_sequencial' === as_tag)
                this.automacao_coleta_sequencial = as_value;

            else if	('transacao_comprovante_1via' === as_tag)
                this.transacao_comprovante_1via	=	as_value;

            else if	('transacao_comprovante_2via' === as_tag)
                this.transacao_comprovante_2via	=	as_value;

            else if	('transacao_comprovante_resumido' === as_tag)
                this.transacao_comprovante_resumido	=	as_value;

            else if	('servico' === as_tag)
                this.servico = as_value;


            else if	('transacao' === as_tag)
                this.transacao = as_value;

            else if	('transacao_produto' === as_tag)
                this.transacao_produto = as_value;

            else if	('retorno' === as_tag)
                this.retorno = as_value;

            else if	('mensagem' === as_tag)
                this.mensagem = as_value;

            else if	('sequencial' === as_tag)
                this.sequencial = parseInt(as_value,0);

            else if	('automacao_coleta_palavra_chave' === as_tag)
                this.automacao_coleta_palavra_chave = as_value;
        }

        this.TagsInicializar = function()
        {
            this.transacao_comprovante_1via = '';
            this.transacao_comprovante_2via = '';
            this.transacao = '';
            this.transacao_produto = '';
            this.servico = '';
            this.retorno = 0;
            this.sequencial = 0;
        }
    }

    function ServicoDesmontar(ao_servico) {

        var
            ln_start = 0;

        var
            ln_end = ao_servico.toString().indexOf("\n\r\n\t\t\r\n\t\t\t\r\n\t\t\r\n\t");

        var
            ls_tag = "";

        var
            ls_value = "";

        var
            ln_value_end = 0;

        try {
            //
            // Enquanto não finalizou a leitura do pacote recebido...
            //
            while (ln_start < ln_end) {
                //
                // Recupera a TAG..
                //
                ls_tag = ao_servico.toString().substring(ln_start, ao_servico.indexOf('="', ln_start));

                //
                // Ignora o = e a primeira " (...="...).
                //
                ln_start = ln_start + (ls_tag.toString().length) + 2;

                //
                // Recupera o valor da tag.
                //
                ls_value = ao_servico.toString().substring(
                    ln_start,(ln_start = ao_servico.toString().indexOf('\"\n', ln_start)));
                //
                //Aponta para a segunda aspa dupla + \n.
                //
                ln_start += 2;

                //
                // Alimenta com a tag recebida..
                //
                io_tags.TagsAlimentar(ls_tag, ls_value);
            }

            if (io_tags.servico !== '') {
                //
                // Se Recebeu um Serviço Executar..
                //
                if (
                    'consultarconsultar' === io_tags.servico
                ) {
                    //
                    // Quebra no ; a lista que a automação recebeu..
                    //
                    var
                        ls_valores = io_tags.transacao.split(';');

                    // Adiciona os tipos de Transação..
                    for (ln_1 = 0; ln_1 < ls_valores.length; ln_1++)
                    {
                        var lo_option = document.createElement('option');

                        lo_option.text = ls_valores[ln_1].replace('"', '').replace('"', '');
                        // lo_lst_obj.options.add(lo_option);
                    }

                    //
                    // Adiciona os Produto..
                    //
                    var
                        ls_valores = io_tags.transacao_produto.split(';');

                    // var
                        // lo_lst_obj = document.getElementById('io_lst_tipo_produto');

                    for (
                        ln_1 = 0
                        ;
                        ln_1 < ls_valores.length
                        ;
                        ln_1++
                    ) {
                        var
                            lo_option = document.createElement('option');
                        //Trace('Valores: '+ls_valores[ln_1]);
                        lo_option.text = ls_valores[ln_1].replace('"', '').replace('"', '');
                        // lo_lst_obj.options.add(lo_option);
                    }
                }
            }
        }
        catch (err) {
            alert('Error interno: ' + err.message);
        }
    }
    //
        // 	function			JanelaFechar()
        // 	{
        // 		Trace('Disconnect...');
        // 		io_connection.close();
        // 	}
    //
        // 	function			JanelaAbrir()
        // 	{
        // 		Trace('Iniciando Aplicação Comercial...');
    //
        // 		var
        // 		loc			=		location.search.substring(1, location.search.length);
    //
        // 		Trace(loc);
        // 	}
        // }

    function Coleta(ao_event)
    {
        if(ao_event == '')
        {
            Send('automacao_coleta_sequencial="'+in_sequencial_executar+'"automacao_coleta_retorno="0"automacao_coleta_informacao="'+ ls_transacao_valor_global+ '"');
        }
    }

    function Confirmar(sequencial)
    {
        // var ls_tipo_transacao = document.getElementById('io_lst_transacao_tipo').options[io_lst_transacao_tipo.selectedIndex].text;
        var ls_tipo_transacao = "Cartao Vender";

        var ls_tags_executar = 'servico="executar"retorno="0"sequencial="'+ sequencial + '"';

        ls_tipo_transacao = 'transacao="'+ls_tipo_transacao+'"';
        ls_tags_executar = ls_tags_executar+ls_tipo_transacao;

        Send(ls_tags_executar);
    }

    function Executar()
    {

        var ls_tags_executar = 'servico="executar"retorno="1"sequencial="'+ Sequencial() +'"';

        var ls_tipo_cartao = "Credito";

         // var ls_tipo_cartao = document.getElementById('io_lst_tipo_cartao').options[io_lst_tipo_cartao.selectedIndex].text;

         // var ls_tipo_transacao = document.getElementById('io_lst_transacao_tipo').options[io_lst_transacao_tipo.selectedIndex].text;

        var ls_tipo_transacao = "Cartao Vender";

         // var ls_tipo_produto = document.getElementById('io_lst_tipo_produto').options[io_lst_tipo_produto.selectedIndex].text;
        var ls_tipo_produto = "Credito-Banrisul";

         // var ls_transacao_pagamento	= document.getElementById('io_lst_transacao_pagamento').options[io_lst_transacao_pagamento.selectedIndex].text;
        var ls_transacao_pagamento	= "A vista";
        // var ls_transacao_valor	= document.getElementById('io_txt_coleta_valor').value;
        var ls_transacao_valor = "";


         if (ls_transacao_valor_global	!==	"")
         {
             ls_transacao_valor_global		=	'transacao_valor="'+ls_transacao_valor_global+'"';
             ls_tags_executar		=	 ls_tags_executar+ls_transacao_valor_global;
         }


         // if	(io_lst_transacao_tipo.selectedIndex >=	0)
         if	(ls_tipo_transacao != "")
         {
             ls_tipo_transacao = 'transacao="'+ls_tipo_transacao+'"';
             ls_tags_executar = ls_tags_executar+ls_tipo_transacao;
         }

         // if	(io_lst_tipo_cartao.selectedIndex >= 0)
         if	(ls_tipo_cartao != "")
         {
             ls_tipo_cartao	 = 'transacao_tipo_cartao="'+ls_tipo_cartao+'"';
             ls_tags_executar =	ls_tags_executar+ls_tipo_cartao;

         }

         // if	( io_lst_transacao_pagamento.selectedIndex >= 0)
         if	( ls_transacao_pagamento != "")
         {
             ls_transacao_pagamento		=	'transacao_pagamento="'+ls_transacao_pagamento+'"';
             ls_tags_executar			=	ls_tags_executar+ls_transacao_pagamento;
         }

         // if	( io_lst_tipo_produto.selectedIndex >= 0 )
         if	( ls_tipo_produto != "" )
         {
             ls_tipo_produto		=	'transacao_produto="'+ls_tipo_produto+'"';
             ls_tags_executar			=	ls_tags_executar+ls_tipo_produto;
         }


         //Envia o pacote para o V$PagueClient.

         Send(ls_tags_executar);
    }

    // Função para envio dos dados.
    function Send(as_buffer)
    {
        // Envia o pacote.
        io_connection.send(as_buffer);

        // Coloca a transação atual na fila
        fila_transacoes.push(as_buffer);
        Trace("Send >>> " + as_buffer);
    }

    function Finalizar()
    {
        Send('servico="finalizar"sequencial="'+Sequencial()+'"retorno="1"');
    }

    function Consultar()
    {
        Send('servico="consultar"retorno="0"sequencial="'+ Sequencial()+'"');
    }

    function Sequencial()
    {
        // Incrementa o sequencial..
        in_sequencial = (in_sequencial+1);

        // document.getElementById('io_txt_sequencial').value = in_sequencial;
        return(in_sequencial);
    }

    function refaz_transacao(retorno_sequencial){
        if(fila_transacoes.length > 0){
            setTimeout(function(){
                fila_transacoes[fila_transacoes.length-1] = fila_transacoes[fila_transacoes.length-1].replace(/sequencial="\d+"/, "sequencial=\"" + retorno_sequencial + "\"");
                    Send(fila_transacoes[fila_transacoes.length-1]);
                }, 2000);
        }
    }

    function inicia_pagamento()
    {

        Consultar();

        setTimeout(function(){

            if ((io_tags.servico !== '') && ('consultar' === io_tags.servico)
                && (io_tags.transacao_produto != '')){

                Executar();
            }
        }, 3000);
    }

    module.PaymentScreenWidget.include({
        render_paymentline: function(line){
            el_node = this._super(line);
            var self = this;

            if (line.cashregister.journal.payment_mode && this.pos.config.iface_tef){

                el_node.querySelector('.payment-terminal-transaction-start')
                    .addEventListener('click', function(){inicia_pagamento()});
                }
            return el_node;
        },
    });
};