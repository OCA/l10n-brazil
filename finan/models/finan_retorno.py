# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals

from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning as UserError
import base64
from StringIO import StringIO
from pybrasil.febraban import BANCO_CODIGO
from pybrasil.febraban import RetornoBoleto
from pybrasil.febraban import gera_pdf_boletos
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D
from ..constantes import *


class finan_retorno_item(models.Model):
    _name = b'finan.retorno_item'
    _description = 'Item de retorno de cobrança'
    _order = 'retorno_id, lancamento_id'
    _rec_name = 'lancamento_id'

    retorno_id = fields.Many2one(
        comodel_name='finan.retorno',
        string='Arquivo de remessa',
        ondelete='cascade',
    )

    comando = fields.Selection(
        selection=[
            ('L', 'Liquidação conciliada'),
            ('Q', 'Liquidaçaõ a conciliar'),
            ('B', 'Baixa'),
            ('N', 'Liquidação a conciliar - cliente negativado'),
            ('R', 'Registro do boleto'),
        ],
        string='Comando',
        default='L',
    )

    lancamento_id = fields.Many2one(
        comodel_name='finan.lancamento',
        string='Lançamento Financeiro',
    )

    quitacao_duplicada = fields.Boolean(
        string='Quitação duplicada?',
        index=False,
    )

    data_vencimento = fields.Date(
        related='lancamento_id.data_vencimento',
        string='Data de vencimento',
    )

    nosso_numero = fields.Char(
        related='lancamento_id.nosso_numero',
        string = 'Nosso número',
    )

    partner_id = fields.Many2one(
        related='lancamento_id.partner_id',
        comodel_name='res.partner',
        string='Participante',
    )

    data_pagamento = fields.Date(
        related='lancamento_id.data_pagamento',
        string='Data quitação',
    )

    data = fields.Date(
        # related='lancamento_id.data',
        string='Data conciliação',
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )

    vr_documento = fields.Monetary(
        related='lancamento_id.vr_documento',
        string='Valor documento',
    )

    valor_multa = fields.Float(
        compute='compute_valor_multa',
        string='Multa',
    )

    valor_juros = fields.Float(
        compute='compute_valor_multa',
        string='Juros',
    )

    valor_desconto = fields.Float(
        compute='compute_valor_multa',
        string='Desconto',
    )

    outros_debitos = fields.Float(
        compute='compute_valor_multa',
        string='Tarifas',
    )

    valor = fields.Float(
        compute='compute_valor_multa',
        string='Valor',
    )

    @api.multi
    def compute_valor_multa(self):
        res = {}
        return 3
        for item_obj in self:
            valor = D(0)

            if item_obj.comando in ['L', 'Q']:
                if nome_campo in ['valor', 'valor_multa',
                                  'valor_juros', 'valor_desconto'
                                  ] and item_obj.comando == 'L':
                    valor = getattr(item_obj.lancamento_id, nome_campo, D(0))
                elif nome_campo not in ['valor', 'valor_multa', 'valor_juros',
                                        'valor_desconto']:
                    valor = getattr(item_obj.lancamento_id, nome_campo, D(0))

            res[item_obj.id] = valor

        return res

class finan_retorno(models.Model):
    _name = b'finan.retorno'
    _description = 'Retornos de cobrança'
    _order = 'data desc, numero_arquivo desc'
    _rec_name = 'numero_arquivo'

    carteira_id = fields.Many2one(
        comodel_name='finan.carteira',
        string='Carteira',
        required=True,
        index=True,
    )

    numero_arquivo = fields.Integer(
        string='Número do arquivo',
    )

    data = fields.Datetime(
        string='Data',
        default=fields.Datetime.now,
        required=True,
    )

    retorno_item_ids = fields.One2many(
        comodel_name='finan.retorno_item',
        inverse_name='retorno_id',
        string='Boletos no retorno',
    )

    arquivo_binario = fields.Binary(
        string='Arquivo',
    )

    lancamento_ids = fields.Many2many(
        comodel_name='finan.lancamento',
        relation='finan_retorno_lancamento',
        column1='retorno_id',
        column2='lancamento_id',
        string='Itens do Retorno',
    )


    @api.multi
    def validacao_banco_carteira(self, arquivo_retorno):
        """
        Validar se o arquivo de retorno tem o mesmo banco da carteira
        """
        # Se o código do banco for diferente
        #
        if arquivo_retorno.banco.codigo != self.carteira_id.banco_id.banco:

            # Se for do caso que o unicred gera o boleto pelo banco bradesco
            # FINAN_BANCO_UNICRED == 136
            # FINAN_BANCO_BRADESCO == 237
            if arquivo_retorno.banco.codigo == '237' and \
                            self.carteira_id.banco_id.banco != '136':

                # TODO: Melhorar mensagem de erro exibindo o nome do banco
                #
                raise UserError('O arquivo é de outro banco - {banco}!'.
                                format(banco=arquivo_retorno.banco.codigo))

    @api.multi
    def get_arquivo(self):
        """
        Método para obter o arquivo apartir do arquivo retornado peo banco
        """

        # Rotina para validar a existencia do arquivo
        #
        if not self.arquivo_binario:
            raise UserError('Nenhum arquivo informado!')

        #
        #
        arquivo_texto = base64.decodestring(self.arquivo_binario)
        arquivo = StringIO()
        arquivo.write(arquivo_texto)
        arquivo.seek(0)

        # Classe de retorno de boletos utilizada pela pybrasil
        #
        arquivo_retorno = RetornoBoleto()

        # Validação da instancia da classe baseada no arquivo de retorno
        #
        if not arquivo_retorno.arquivo_retorno(arquivo):
            raise UserError('Formato do arquivo incorreto ou inválido!')

        return arquivo_retorno

    @api.multi
    def processar_retorno(self):
        """
        Método para processamento do CNAB
        """

        self.ensure_one()

        # Gambiarra temporaria para nao quebrar o código
        #
        retorno_id = self

        # Gerar objeto apartir do arquivo upado
        #
        arquivo_retorno = self.get_arquivo()

        # Validar se o arquivo de retorno tem o mesmo banco da carteira
        #
        if arquivo_retorno.banco.codigo != \
                retorno_id.carteira_id.banco_id.banco:

            if arquivo_retorno.banco.codigo == '237' and \
                            retorno_id.carteira_id.banco_id.banco != '136':
                raise UserError('O arquivo é de outro banco - {banco}!'.
                                format(banco=arquivo_retorno.banco.codigo))

        # Retorno do banco do brasil nao retorna o cnpj do beneficiario
        #
        if arquivo_retorno.banco.codigo != FINAN_BANCO_BRASIL:

            # Validar se o beneficiario do arquivo de retorno é o
            # titular da conta bancaria na carteira selecionada
            #
            if arquivo_retorno.beneficiario.cnpj_cpf != \
                    retorno_id.carteira_id.banco_id.titular_id.cnpj_cpf:

                # Se na carteira for definido um sacador, o cnpj do
                # beneficiario do arquivo de retorno devera ser igual ao
                # cnpj do sacor da carteira
                #
                if retorno_id.carteira_id.sacador_id:
                    if arquivo_retorno.beneficiario.cnpj_cpf != \
                            retorno_id.carteira_id.sacador_id.cnpj_cpf:

                        erro = 'O arquivo é de outro beneficiário! \n ' \
                               'Arquivo retorno: {name_ret} - {cnpj_ret} \n' \
                               'Carteira: {name_cart} - {cnpj_cart}'.format(
                            name_ret=arquivo_retorno.beneficiario.nome,
                            cnpj_ret=arquivo_retorno.beneficiario.cnpj_cpf,
                            name_cart=retorno_id.carteira_id.sacador_id.cnpj_cpf,
                            cnpj_cart=retorno_id.carteira_id.sacador_id.nome
                        )


                        raise UserError(erro)

                # Se tiver cnpj diferentes e nao for definido o sacador
                #
                else:
                    erro = 'O arquivo é de outro beneficiário! \n ' \
                           'Arquivo retorno: {name_ret} - {cnpj_ret} \n' \
                           'Carteira: {name_cart} - {cnpj_cart}'.format(
                        name_ret=arquivo_retorno.carteira_id.banco_id.titular_id.nome,
                        cnpj_ret=arquivo_retorno.carteira_id.banco_id.titular_id.cnpj_cpf,
                        name_cart=retorno_id.beneficiario.name,
                        cnpj_cart=retorno_id.beneficiario.cnpj_cpf
                    )
                    raise UserError(erro)

        # Validação de Agência - conta
        #
        if arquivo_retorno.banco.codigo not in ('748', '104','001'):
            if arquivo_retorno.beneficiario.agencia.numero != \
                    retorno_id.carteira_id.banco_id.agencia:
                erro = 'O arquivo é de outra agência! \n' \
                       'Agência do beneficiario: {agencia_ben} \n' \
                       'Arquivo de retorno: {agencia_ret} \n'.format(
                    agencia_ben=retorno_id.carteira_id.banco_id.agencia,
                    agencia_ret=arquivo_retorno.beneficiario.agencia.numero
                )
                raise UserError(erro)

            if arquivo_retorno.beneficiario.conta.numero != retorno_id.\
                    carteira_id.banco_id.agencia:
                try:
                    if int(arquivo_retorno.beneficiario.conta.numero) != int(
                            retorno_id.carteira_id.banco_id.conta):
                        raise UserError('O arquivo é de outra conta - '
                                        '{conta}!'.format(conta=arquivo_retorno.
                                                          beneficiario.
                                                          conta.numero))
                except:
                    raise UserError('O arquivo é de outra conta - {conta}!'
                                    ''.format(conta=arquivo_retorno.beneficiario.
                                              conta.numero))

        # Se o codigo do beneficiario for diferente na carteira e no arq.
        #
        if arquivo_retorno.beneficiario.codigo.numero != \
                retorno_id.carteira_id.beneficiario:

            # Se o arq de retorno tiver numero_beneficiario_unicred
            #
            unicred = hasattr(
                arquivo_retorno.boletos[1],'numero_beneficiario_unicred') and \
                      arquivo_retorno.boletos[1].numero_beneficiario_unicred
            if len(arquivo_retorno.boletos) > 1 and unicred:

                # O beneficiario unicred devera ser igual ao beneficiario
                # da carteira


                beneciario_carteira = retorno_id.carteira_id.beneficiario
                beneficiario_unicred = \
                    arquivo_retorno.boletos[1].numero_beneficiario_unicred

                if beneficiario_unicred != beneciario_carteira:
                    msg_erro = \
                        'O codigo de beneficiario da carteira cadastrado' \
                        ' no sistema ({beneficiario}), difere do codigo ' \
                        ' de beneficiario Unicred do arquivo: {unicred}.'.\
                            format(
                                beneficiario=beneciario_carteira,
                                unicred = beneficiario_unicred,
                            )
                    raise UserError(msg_erro)
            else:
                try:
                    if int(arquivo_retorno.beneficiario.codigo_beneficiario.numero
                           ) != int(retorno_id.carteira_id.beneficiario):
                        raise UserError('O arquivo é de outra código '
                                        'beneficiário - {bene}!'.format(
                            bene=arquivo_retorno.beneficiario.codigo_beneficiario.
                                numero))
                except:
                    raise UserError('O arquivo é de outra código '
                                    'beneficiário - {bene}!'.format(
                        bene=arquivo_retorno.beneficiario.codigo_beneficiario.
                            numero))

        # Validar se ja foi gerado um retorno com mesma sequencia e da
        # mesma carteira
        ids = self.search([
            ('numero_arquivo','=', arquivo_retorno.sequencia),
            ('carteira_id','=',retorno_id.carteira_id.id),
        ])
        if ids:
            raise UserError(
                'Arquivo já existente - Nº {numero_arquivo}!'.format(
                    numero_arquivo=arquivo_retorno.sequencia))

        # Escrever o numero do arquivo e a data que foi gerado
        retorno_id.write({
            'numero_arquivo': arquivo_retorno.sequencia,
            'data': str(arquivo_retorno.data_hora)
        })

        lancamento_obj = self.env.get('finan.lancamento')

        #
        # Remove os boletos anteriores
        #
        # ??? Remover esses caras?
        retorno_id.retorno_item_ids.unlink()

        #
        # Exclui os retornos já existentes deste arquivo
        #
        # self._cr.execute("update finan_lancamento set numero_documento = "
        #                  "'QUERO EXCLUIR' where tipo = 'PR' and retorno_id"
        #                  " = " + str(retorno_id.id) + ";")
        # self._cr.execute("delete from finan_lancamento where tipo = 'PR' "
        #                  "and retorno_id = " + str(retorno_id.id) + ";")
        # self._cr.commit()

        #
        # Adiciona os comandos separados para baixa/Liquidação de cliente
        # negativado
        #
        for comando in arquivo_retorno.banco.comandos_liquidacao:
            if comando + '-N' not in \
                    arquivo_retorno.banco.descricao_comandos_retorno:
                arquivo_retorno.banco.descricao_comandos_retorno[comando +'-N'] = \
                    arquivo_retorno.banco.descricao_comandos_retorno[comando] + \
                    ' - cliente negativado'

        # Preencher a identificação na remessa(5 caracteres as vezes menos)

        #
        # Processa os boletos do arquivo
        #
        for boleto in arquivo_retorno.boletos:

            if boleto.identificacao.upper().startswith('N'):

                lancamento_id = int(boleto.identificacao.upper().replace('N', ''))

                lancamento_ids = lancamento_obj.search((
                    'carteira_id', '=', retorno_id.carteira_id.id),
                    ('id', '=', lancamento_id))

            elif boleto.identificacao.upper().startswith('ID'):

                lancamento_id = int(boleto.identificacao.upper().replace('ID', ''), 36)

                lancamento_ids = lancamento_obj.search(
                    ('carteira_id', '=', retorno_id.carteira_id.id),
                    ('id', '=', lancamento_id))


            else:
                print (boleto.nosso_numero)
                lancamento_ids = lancamento_obj.search([
                    ('carteira_id', '=', retorno_id.carteira_id.id),
                    ('nosso_numero', '=', boleto.nosso_numero)
                ], order='data_vencimento desc')

            if lancamento_ids:
                lancamento_id = lancamento_ids[0]
            else:
                lancamento_id = False

            comando = ''
            #
            # Trata aqui a liquidação sem data de crédito do SICOOB
            # (título antecipado pelo banco)
            #
            if arquivo_retorno.banco.codigo == '756' and boleto.comando == '06' and boleto.data_credito is None:
                boleto.comando += '.1'

            if boleto.comando in arquivo_retorno.banco.comandos_liquidacao:
                if arquivo_retorno.banco.comandos_liquidacao[boleto.comando]:
                    comando = 'L'
                else:
                    comando = 'Q'

            elif boleto.comando in arquivo_retorno.banco.comandos_baixa:

                comando = 'B'

            # banco emite - banco que da o nosso numero
            elif retorno_id.carteira_id.banco_emite and boleto.comando == '02':

                comando = 'R'

            if lancamento_id:
                boleto.pagador.cnpj_cpf = lancamento_id.participante_id.cnpj_cpf
                boleto.pagador.nome = lancamento_id.participante_id.name
                boleto.documento.numero = lancamento_id.numero

                #
                # Cliente negativado não baixa automático o boleto
                #
                # if comando != 'B' and lancamento_id.forma_pagamento_id and lancamento_id.forma_pagamento_id.cliente_negativado:
                #     comando = 'N'
                #     boleto.comando += '-N'

                if retorno_id.carteira_id.banco_emite and comando == 'R':
                    dados = {'nosso_numero': boleto.nosso_numero}
                    comando = 'R'
                    lancamento_id.write(dados)

            if lancamento_id and comando:
                dados = {
                    'retorno_id': retorno_id.id,
                    'comando': comando,
                    'lancamento_id': lancamento_id.id,
                }
                item_id = self.env.get('finan.retorno_item').create(dados)

                # Não processa se já estiver quitado
                #
                if lancamento_id.state not in ['A vencer', 'Vencido', 'Vence hoje']:
                    if lancamento_id.data_baixa and parse_datetime(lancamento_id.data_baixa).date() != boleto.data_ocorrencia:
                        item_id.write({'quitacao_duplicada': True})
                        boleto.pagamento_duplicado = True
                        continue

                #
                # Deleta os pagamentos anteriores
                # ??? Nao entendi
                #
                # pag_ids = lancamento_obj.search([
                #     ('tipo', '=', 'pagamento'),
                #     ('lancamento_id', '=', lancamento_id.id),
                #     ('retorno_id', '=', retorno_id.id),
                #     ('retorno_item_id', '=', item_id),
                # ])
                # lancamento_obj.unlink(pag_ids)

                #
                #
                #
                forma_pagamento_obj = self.env.get('finan.forma.pagamento')

                if comando in ('B', 'N', 'R'):
                    dados = {
                        #'data_baixa': boleto.data_
                    }
                else:
                    dados = {
                        'valor_desconto': boleto.valor_desconto,
                        'valor_juros': boleto.valor_juros,
                        'valor_multa': boleto.valor_multa,
                        'outros_debitos': boleto.valor_despesa_cobranca,
                        'valor': boleto.valor_recebido,
                        'data_pagamento': str(boleto.data_ocorrencia)[:10],
                        'forma_pagamento_id': lancamento_id.forma_pagamento_id.id,
                    }

                    if comando == 'L':
                        dados['data'] = str(boleto.data_credito)[:10]
                        dados['conciliado'] = True

                    #print('lancamento id', lancamento_obj.id,
                        # 'data_quitacao', str(
                        # boleto.data_ocorrencia)[:10], 'data_credito',
                        # str(boleto.data_credito)[:10])

                dados['baixa_boleto'] = True
                lancamento_id.write(dados)

                if comando in ('B', 'R'):
                    pass
                else:
                    #
                    # Cria agora o pagamento em si
                    #
                    dados_pagamento = {
                        'tipo': 'pagamento',
                        'lancamento_id': lancamento_id.id,
                        'company_id': lancamento_id.company_id.id,
                        'vr_documento': lancamento_id.vr_documento,
                        'data_pagamento': str(boleto.data_ocorrencia)[:10],
                        'data_juros': str(boleto.data_ocorrencia)[:10],
                        'data_multa': str(boleto.data_ocorrencia)[:10],
                        'data_desconto': str(boleto.data_ocorrencia)[:10],
                        'valor_desconto': boleto.valor_desconto,
                        'valor_juros': boleto.valor_juros,
                        'valor_multa': boleto.valor_multa,
                        'outros_debitos': boleto.valor_despesa_cobranca,
                        'valor': boleto.valor_recebido,
                        'banco_id': retorno_id.carteira_id.banco_id.id,
                        'carteira_id': retorno_id.carteira_id.id,
                        'forma_pagamento_id': lancamento_id.forma_pagamento_id.id,
                        'retorno_id': retorno_id.id,
                        'conta_id': 308,
                    }

                    if comando == 'L':
                        dados_pagamento['data'] = str(boleto.data_credito)[:10]
                        dados_pagamento['conciliado'] = True

                    dados['baixa_boleto'] = True
                    pr_id = lancamento_obj.create(dados_pagamento)

                    print('pagamento id', pr_id, 'data_pagamento',
                          str(boleto.data_ocorrencia)[:10], 'data_credito',
                          str(boleto.data_credito)[:10])

        # Nao existe essa função
        #

        #
        # Anexa os boletos em PDF ao registro da remessa
        #
        # attachment_obj = self.env.get('ir.attachment')
        # attachment_ids = attachment_obj.search([
        #     ('res_model', '=', 'finan.retorno'),
        #     ('res_id', '=', retorno_id.id),
        #     ('name', '=', 'francesinha.pdf')
        # ])
        # #
        # # Apaga os boletos anteriores com o mesmo nome
        # #
        # attachment_obj.unlink(attachment_ids)
        #
        # dados = {
        #     'datas': base64.encodestring(pdf),
        #     'name': 'francesinha.pdf',
        #     'datas_fname': 'francesinha.pdf',
        #     'res_model': 'finan.retorno',
        #     'res_id': retorno_id.id,
        #     'file_type': 'application/pdf',
        # }
        # attachment_pool.create(dados)

            #numero_arquivo = int(
        # retorno_id.carteira_id.ultimo_arquivo_retorno) + 1
            #self.write(cr, uid, [retorno_id.id], {
        # 'numero_arquivo': str(numero_arquivo)})
            #self.pool.get('finan.carteira').write(
        # cr, 1, [retorno_id.carteira_id.id], {
        # 'ultimo_arquivo_retorno': str(numero_arquivo)})
        #else:
            #numero_arquivo = int(retorno_id.numero_arquivo)

        ##
        ## Gera os boletos
        ##
        #lista_boletos = []
        #for lancamento_obj in retorno_id.lancamento_ids:
            #boleto = lancamento_obj.gerar_boleto()
            #lista_boletos.append(boleto)

        #pdf = gera_boletos_pdf(lista_boletos)
        #nome_boleto = 'boletos_' +
        # retorno_id.carteira_id.banco_id.bank_name + '_' +
        # str(retorno_id.data) + '.pdf'

        ##
        ## Anexa os boletos em PDF ao registro da remessa
        ##
        #attachment_pool = self.pool.get('ir.attachment')
        #attachment_ids = attachment_pool.search(cr, uid, [(
        # 'res_model', '=', 'finan.retorno'), (
        # 'res_id', '=', retorno_id.id), ('name', '=', nome_boleto)])
        ##
        ## Apaga os boletos anteriores com o mesmo nome
        ##
        #attachment_pool.unlink(cr, uid, attachment_ids)

        #dados = {
            #'datas': base64.encodestring(pdf),
            #'name': nome_boleto,
            #'datas_fname': nome_boleto,
            #'res_model': 'finan.retorno',
            #'res_id': retorno_id.id,
            #'file_type': 'application/pdf',
        #}
        #attachment_pool.create(cr, uid, dados)

        #
        # Gera a remessa propriamente dita
        #
        # remessa = Remessa()
        # remessa.tipo = 'CNAB_400'
        # remessa.boletos = lista_boletos
        # remessa.sequencia = numero_arquivo
        # remessa.data_hora = datetime.strptime(retorno_id.data,
        # '%Y-%m-%d %H:%M:%S')
        #
        # #
        # # Nomenclatura bradesco
        # #
        # if lista_boletos[0].banco.codigo == '237':
        #     nome_retorno = 'CB' + remessa.data_hora.strftime('%d%m')
        # + str(remessa.sequencia).zfill(2) + '.txt'
        # else:
        #     nome_retorno = unicode(
        # retorno_id.carteira_id.nome).encode('utf-8') + '_retorno_' +
        # str(numero_arquivo) + '.txt'
        #
        # #
        # # Anexa a remessa ao registro da remessa
        # #
        # attachment_pool = self.pool.get('ir.attachment')
        # attachment_ids = attachment_pool.search(cr, uid, [('res_model',
        # '=', 'finan.retorno'), ('res_id', '=', retorno_id.id), ('name',
        # '=', nome_retorno)])
        # #
        # # Apaga os boletos anteriores com o mesmo nome
        # #
        # attachment_pool.unlink(cr, uid, attachment_ids)
        #
        # dados = {
        #     'datas': base64.encodestring(remessa.arquivo_retorno),
        #     'name': nome_retorno,
        #     'datas_fname': nome_retorno,
        #     'res_model': 'finan.retorno',
        #     'res_id': retorno_id.id,
        #     'file_type': 'text/plain',
        # }
        # attachment_pool.create(cr, uid, dados)

    # def gerar_retorno_anexo(self, cr, uid, ids, context=None):
    #     for id in ids:
    #         self.gerar_retorno(cr, uid, id)

