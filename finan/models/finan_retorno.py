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

class finan_retorno_item(models.Model):
    _name = b'finan.retorno_item'
    _description = 'Item de retorno de cobrança'
    _order = 'retorno_id, lancamento_id'
    _rec_name = 'lancamento_id'

    def _valor(self, nome_campo, args=None):
        res = {}

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

    #'retorno_id': fields.many2one('finan.retorno', 'Arquivo de remessa',
    #  ondelete='cascade'),
    retorno_id = fields.Many2one(

        comodel_name='finan.retorno',
        string='Arquivo de remessa',
        ondelete='cascade',
    )

    #    'comando': fields.selection((('L', 'Liquidação conciliada'), ('Q',
    # 'Liquidação a conciliar'),
    # ('B', 'Baixa'), ('N', 'Liquidação a conciliar - cliente negativado'),
    # ('R', 'Registro do boleto')), 'Comando'),
    comando = fields.Selection(
        selection=[
            ('L', 'Liquidação conciliada'),
            ('Q', 'Liquidaçaõ a conciliar'),
            ('B', 'Baixa'),
            ('N', 'Liquidação a conciliar - cliente negativado'),
            ('R', 'Registro do boleto')

        ],
        string='Comando',
        default = 'L',
    )
    #    'lancamento_id': fields.many2one(u'finan.lancamento', u'Boleto'),
    lancamento_id = fields.Many2one(
       'finan.lancamento',
       string = 'Lançamento Financeiro',
    )
    #    'quitacao_duplicada': fields.boolean(u'Quitação duplicada?'),
    quitacao_duplicada = fields.Boolean(
        string='Quitação duplicada?',
        index=False,
    )
    #    'data_vencimento': fields.related('lancamento_id', 'data_vencimento', type='date',
    # relation='finan.lancamento', string=u'Data de vencimento', store=False),
    data_vencimento = fields.Date(
        related = 'lancamento_id.data_vencimento',
        relation = 'finan.lancamento',
        string = 'Data de vencimento',
        store = False,
    )
    #    'nosso_numero': fields.related('lancamento_id', 'nosso_numero', type='char',
    # relation='finan.lancamento', string=u'Nosso número', store=False),
    nosso_numero = fields.Char(
        related = 'lancamento_id.nosso_numero',
        relation = 'finan.lancamento',
        string = 'Nosso número',
        store = False,
    )
    #    'partner_id': fields.related('lancamento_id', 'partner_id', type='many2one', relation='res.partner',
    #  string=u'Cliente', store=False),
    partner_id = fields.Many2one(
        related = 'lancamento_id.partner_id',
        relation = 'res.partner',
        string = 'Cliente',
        store = False,
    )
    #    'data_quitacao': fields.related('lancamento_id', 'data_quitacao', type='date',
    # relation='finan.lancamento', string=u'Data quitação', store=False),
    data_pagamento = fields.Date(
        related = 'lancamento_id.data_pagamento',
        relation = 'finan.lancamento',
        string = 'Data quitação',
        store = False,
    )
    #    'data': fields.related('lancamento_id', 'data', type='date',
    # relation='finan.lancamento',
    # string=u'Data conciliação', store=False),
    # data = fields.Date(
    #     related = 'lancamento_id.data',
    #     relation= 'finan.lancamento',
    #     string = 'Data conciliação',
    #     store = False,
    # )
    #    'valor_documento': fields.related('lancamento_id', 'valor_documento',
    # type='float', relation='finan.lancamento', string=u'Valor documento',
    # store=False),
    vr_documento = fields.Monetary(
        related = 'lancamento_id.vr_documento',
        relation = 'finan.lancamento',
        string = 'Valor documento',
        store = False,
    )

    #'valor_multa': fields.function(_valor, type='float', string=u'Multa',
    # store=False),
    valor_multa = fields.Float(
        function = '_valor',
        string  = 'Multa',
        store = False,
    )
    #'valor_juros': fields.function(_valor, type='float', string=u'Juros',
    #  store=False),
    valor_juros = fields.Float(
        function='_valor',
        string='Juros',
        store=False,
    )
    #'valor_desconto': fields.function(_valor, type='float', string='Desconto',
    #  store=False),
    valor_desconto = fields.Float(
        function='_valor',
        string='Desconto',
        store=False,
    )
    #'outros_debitos': fields.function(_valor, type='float', string=u'Tarifa',
    # store=False),
    outros_debitos = fields.Float(
        function='_valor',
        string='Tarifas',
        store=False,
    )
    # 'valor': fields.function(_valor, type='float', string=u'Valor',
    # store=False),
    valor = fields.Float(
        function='_valor',
        string='Valor',
        store=False,
    )

class finan_retorno(models.Model):
    _name = b'finan.retorno'
    _description = 'Retornos de cobrança'
    _order = 'data desc, numero_arquivo desc'
    _rec_name = 'numero_arquivo'

    #       'carteira_id': fields.many2one('finan.carteira', u'Carteira',
    # required=True),
    carteira_id = fields.Many2one(
        comodel_name='finan.carteira',
        string='Carteira',
        required=True,
        index=True,
    )

    #        'numero_arquivo': fields.integer(u'Número do arquivo'),
    numero_arquivo = fields.Integer(
        string = 'Número do arquivo',
    )

    #      'data': fields.datetime(u'Data e hora'),
    data = fields.Datetime(
        string='Data',
        default=fields.Datetime.now,
        required=True,
        index=True,
    )

    #       'retorno_item_ids': fields.one2many('finan.retorno_item',
    # 'retorno_id', u'Boletos no retorno'),
    retorno_item_ids = fields.One2many(
        comodel_name='finan.retorno_item',
        inverse_name='retorno_id',
        string='Boletos no retorno',
    )

    #        'arquivo_binario': fields.binary(u'Arquivo'),
    arquivo_binario = fields.Binary(
        string='Arquivo',
    )

    lancamento_ids = fields.Many2many(
        comodel_name='finan.retorno_item',
        relation='finan_retorno_lancamento',
        column1='retorno_id',
        column2='lancamento_id',
        string='Itens do Retorno',
    )

    @api.multi
    def processar_retorno(self):
        for retorno_obj in self:

            forma_pagamento_pool = self.env['finan.formapagamento']

            if not retorno_obj.arquivo_binario:
                raise UserError('Nenhum arquivo informado!')

            arquivo_texto = base64.decodestring(retorno_obj.arquivo_binario)
            arquivo = StringIO()
            arquivo.write(arquivo_texto)
            arquivo.seek(0)

            retorno = RetornoBoleto()
            if not retorno.arquivo_retorno(arquivo):
                raise UserError('Formato do arquivo incorreto ou inválido!')

            if retorno.banco.codigo != \
                    retorno_obj.carteira_id.res_partner_bank_id.bank_bic:

                if retorno.banco.codigo == '237' and retorno_obj.carteira_id.\
                        res_partner_bank_id.bank_bic != '136':
                    raise UserError('O arquivo é de outro banco - {banco}!'.
                                    format(banco=retorno.banco.codigo))

            if retorno.banco.codigo != '001':
                if retorno.beneficiario.cnpj_cpf != retorno_obj.carteira_id.\
                        res_partner_bank_id.partner_id.cnpj_cpf:
                    if retorno_obj.carteira_id.sacado_id:
                        if retorno.beneficiario.cnpj_cpf != retorno_obj.\
                                carteira_id.sacado_id.cnpj_cpf:
                            raise UserError('O arquivo é de outro beneficiário'
                                            ' - {cnpj}!'.format(
                                cnpj=retorno_obj.carteira_id.sacado_id.
                                    cnpj_cpf))
                            raise UserError('O arquivo é de outro beneficiário'
                                            ' - {cnpj}!'.format(cnpj=retorno.
                                                                beneficiario.
                                                                cnpj_cpf))
                    else:
                        raise UserError('O arquivo é de outro beneficiário - '
                                        '{cnpj}!'.format(cnpj=retorno_obj.
                                                         carteira_id.
                                                         res_partner_bank_id.
                                                         partner_id.cnpj_cpf))
                        raise UserError('O arquivo é de outro beneficiário - '
                                        '{cnpj}!'.format(cnpj=retorno.
                                                         beneficiario.cnpj_cpf)
                                        )


            if retorno.banco.codigo not in ('748', '104','001'):
                if retorno.beneficiario.agencia.numero != retorno_obj.\
                        carteira_id.res_partner_bank_id.agencia:
                    raise UserError('O arquivo é de outra agência - {agencia}!'
                                    ''.format(agencia=retorno.beneficiario.
                                              agencia.numero))

                if retorno.beneficiario.conta.numero != retorno_obj.\
                        carteira_id.res_partner_bank_id.acc_number:
                    try:
                        if int(retorno.beneficiario.conta.numero) != int(
                                retorno_obj.carteira_id.res_partner_bank_id.
                                        acc_number):
                            raise UserError('O arquivo é de outra conta - '
                                            '{conta}!'.format(conta=retorno.
                                                              beneficiario.
                                                              conta.numero))
                    except:
                        raise UserError('O arquivo é de outra conta - {conta}!'
                                        ''.format(conta=retorno.beneficiario.
                                                  conta.numero))

            if retorno.beneficiario.codigo_beneficiario.numero != retorno_obj.\
                    carteira_id.beneficiario:
                if len(retorno.boletos) > 1 and hasattr(retorno.boletos[1],
                                                        'numero_beneficiario_'
                                                        'unicred') and \
                        retorno.boletos[1].numero_beneficiario_unicred:
                    if retorno.boletos[1].numero_beneficiario_unicred != \
                            retorno_obj.carteira_id.beneficiario:
                        raise UserError('O arquivo é de outra código '
                                        'beneficiário - {bene}!'
                                        ''.format(bene=retorno.beneficiario.
                                                  codigo_beneficiario.numero))
                else:
                    try:
                        if int(retorno.beneficiario.codigo_beneficiario.numero
                               ) != int(retorno_obj.carteira_id.beneficiario):
                            raise UserError('O arquivo é de outra código '
                                            'beneficiário - {bene}!'.format(
                                bene=retorno.beneficiario.codigo_beneficiario.
                                    numero))
                    except:
                        raise UserError('O arquivo é de outra código '
                                        'beneficiário - {bene}!'.format(
                            bene=retorno.beneficiario.codigo_beneficiario.
                                numero))

                retorno.beneficiario.conta.numero = retorno_obj.carteira_id.\
                    res_partner_bank_id.acc_number
                retorno.beneficiario.conta.digito = retorno_obj.carteira_id.\
                                                        res_partner_bank_id.\
                                                        conta_digito or ''


            ids = self.search(('numero_arquivo','=', retorno.sequencia),(
                'carteira_id','=',retorno_obj.carteira_id.id))
            if ids:
                raise UserError('Arquivo já existente - Nº {numero_arquivo}!'.
                                format(numero_arquivo=retorno.sequencia))

            retorno_obj.write({'numero_arquivo': retorno.sequencia, 'data':
                str(retorno.data_hora)})

            lancamento_pool = self.pool.get('finan.lancamento')

            #
            # Remove os boletos anteriores
            #
            for item_obj in retorno_obj.retorno_item_ids:
                item_obj.unlink()

            #
            # Exclui os retornos já existentes deste arquivo
            #
            self._cr.execute("update finan_lancamento set numero_documento = "
                             "'QUERO EXCLUIR' where tipo = 'PR' and retorno_id"
                             " = " + str(retorno_obj.id) + ";")
            self._cr.execute("delete from finan_lancamento where tipo = 'PR' "
                             "and retorno_id = " + str(retorno_obj.id) + ";")
            self._cr.commit()

            #
            # Adiciona os comandos separados para baixa/Liquidação de cliente
            # negativado
            #
            for comando in retorno.banco.comandos_liquidacao:
                if comando + '-N' not in \
                        retorno.banco.descricao_comandos_retorno:
                    retorno.banco.descricao_comandos_retorno[comando +'-N'] = \
                        retorno.banco.descricao_comandos_retorno[comando] + \
                        ' - cliente negativado'

            #
            # Processa os boletos do arquivo
            #
            for boleto in retorno.boletos:
                if boleto.identificacao.upper().startswith('ID_'):
                    lancamento_id = int(boleto.identificacao.upper().
                                        replace('ID_', ''))
                    lancamento_ids = lancamento_pool.search((
                        'carteira_id', '=', retorno_obj.carteira_id.id),
                        ('id', '=', lancamento_id))
                elif boleto.identificacao.upper().startswith('IX_'):
                    lancamento_id = int(boleto.identificacao.upper().
                                        replace('IX_', ''), 36)
                    lancamento_ids = lancamento_pool.search(
                        ('carteira_id', '=', retorno_obj.carteira_id.id),
                        ('id', '=', lancamento_id))
                else:
                    lancamento_ids = lancamento_pool.search([
                        ('carteira_id', '=', retorno_obj.carteira_id.id),
                        ('nosso_numero', '=', boleto.nosso_numero)],
                        order='data_vencimento desc')

                if lancamento_ids:
                    lancamento_id = lancamento_ids[0]
                else:
                    lancamento_id = False

                comando = ''
                #
                # Trata aqui a liquidação sem data de crédito do SICOOB
                # (título antecipado pelo banco)
                #
                if retorno.banco.codigo == '756' and boleto.comando ==\
                        '06' and boleto.data_credito is None:
                    boleto.comando += '.1'

                if boleto.comando in retorno.banco.comandos_liquidacao:
                    if retorno.banco.comandos_liquidacao[boleto.comando]:
                        comando = 'L'
                    else:
                        comando = 'Q'
                elif boleto.comando in retorno.banco.comandos_baixa:
                    comando = 'B'
                elif retorno_obj.carteira_id.nosso_numero_pelo_banco and \
                                boleto.comando == '02':
                    comando = 'R'

                if lancamento_id:
                    lancamento_obj = lancamento_pool.browse(lancamento_id)
                    boleto.pagador.cnpj_cpf = lancamento_obj.partner_id.cnpj_cpf
                    boleto.pagador.nome = lancamento_obj.partner_id.name
                    boleto.documento.numero = lancamento_obj.numero_documento

                    #
                    # Cliente negativado não baixa automático o boleto
                    #
                    if comando != 'B' and lancamento_obj.formapagamento_id \
                            and lancamento_obj.formapagamento_id.\
                                    cliente_negativado:
                        comando = 'N'
                        boleto.comando += '-N'

                    if retorno_obj.carteira_id.nosso_numero_pelo_banco and \
                                    comando == 'R':
                        dados = {
                            'nosso_numero': boleto.nosso_numero
                        }
                        comando = 'R'
                        lancamento_obj.write(dados)

                if lancamento_id and comando:
                    dados = {
                        'retorno_id': retorno_obj.id,
                        'comando': comando,
                        'lancamento_id': lancamento_id,
                    }
                    item_id = self.pool.get('finan.retorno_item').create(dados)

                    dados['retorno_item_id'] = item_id

                    #item_obj = self.pool.get('finan.retorno_item').browse(
                    # cr, uid, item_id)

                    ##
                    ## Não processa se já estiver quitado
                    ##
                    #if lancamento_obj.situacao not in ['A vencer', 'Vencido',
                    # 'Vence hoje']:
                        #if lancamento_obj.data_quitacao and parse_datetime(
                    # lancamento_obj.data_quitacao).date() !=
                    # boleto.data_ocorrencia:
                            #item_obj.write({'quitacao_duplicada': True})
                            #boleto.pagamento_duplicado = True
                            #continue

                    #
                    # Deleta os pagamentos anteriores
                    #
                    pag_ids = lancamento_pool.search(('tipo', '=', 'PR'), (
                        'lancamento_id', '=', lancamento_obj.id), (
                        'retorno_id', '=', retorno_obj.id), (
                        'retorno_item_id', '=', item_id))
                    lancamento_pool.unlink(pag_ids)

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
                            'formapagamento_id': forma_pagamento_pool.
                                id_credito_cobranca(),
                        }

                        if comando == 'L':
                            dados['data'] = str(boleto.data_credito)[:10]
                            dados['conciliado'] = True

                        #print('lancamento id', lancamento_obj.id,
                            # 'data_quitacao', str(
                            # boleto.data_ocorrencia)[:10], 'data_credito',
                            # str(boleto.data_credito)[:10])

                    lancamento_obj.write(dados, context={'baixa_boleto': True})

                    if comando in ('B', 'R'):
                        pass
                    else:
                        #
                        # Cria agora o pagamento em si
                        #
                        dados_pagamento = {
                            'tipo': 'PR',
                            'lancamento_id': lancamento_obj.id,
                            'company_id': lancamento_obj.company_id.id,
                            'vr_documento': lancamento_obj.vr_documento,
                            'data_pagamento': str(boleto.data_ocorrencia)[:10],
                            'data_juros': str(boleto.data_ocorrencia)[:10],
                            'data_multa': str(boleto.data_ocorrencia)[:10],
                            'data_desconto': str(boleto.data_ocorrencia)[:10],
                            'valor_desconto': boleto.valor_desconto,
                            'valor_juros': boleto.valor_juros,
                            'valor_multa': boleto.valor_multa,
                            'outros_debitos': boleto.valor_despesa_cobranca,
                            'valor': boleto.valor_recebido,
                            'res_partner_bank_id': retorno_obj.carteira_id.
                                res_partner_bank_id.id,
                            'carteira_id': retorno_obj.carteira_id.id,
                            'formapagamento_id': forma_pagamento_pool.
                                id_credito_cobranca(),
                            'retorno_id': retorno_obj.id,
                        }

                        if comando == 'L':
                            dados_pagamento['data'] = str(boleto.
                                                          data_credito)[:10]
                            dados_pagamento['conciliado'] = True

                        pr_id = lancamento_pool.create(
                            dados_pagamento, context={'baixa_boleto': True})
                        print('pagamento id', pr_id, 'data_pagamento',
                              str(boleto.data_ocorrencia)[:10], 'data_credito',
                              str(boleto.data_credito)[:10])

                self._cr.commit()

            pdf = gera_retorno_pdf(retorno)

            #
            # Anexa os boletos em PDF ao registro da remessa
            #
            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(('res_model', '=',
                                                     'finan.retorno'), (
                'res_id', '=', retorno_obj.id), ('name', '=',
                                                 'francesinha.pdf'))
            #
            # Apaga os boletos anteriores com o mesmo nome
            #
            attachment_pool.unlink(attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': 'francesinha.pdf',
                'datas_fname': 'francesinha.pdf',
                'res_model': 'finan.retorno',
                'res_id': retorno_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(dados)

                #numero_arquivo = int(
            # retorno_obj.carteira_id.ultimo_arquivo_retorno) + 1
                #self.write(cr, uid, [retorno_obj.id], {
            # 'numero_arquivo': str(numero_arquivo)})
                #self.pool.get('finan.carteira').write(
            # cr, 1, [retorno_obj.carteira_id.id], {
            # 'ultimo_arquivo_retorno': str(numero_arquivo)})
            #else:
                #numero_arquivo = int(retorno_obj.numero_arquivo)

            ##
            ## Gera os boletos
            ##
            #lista_boletos = []
            #for lancamento_obj in retorno_obj.lancamento_ids:
                #boleto = lancamento_obj.gerar_boleto()
                #lista_boletos.append(boleto)

            #pdf = gera_boletos_pdf(lista_boletos)
            #nome_boleto = 'boletos_' +
            # retorno_obj.carteira_id.res_partner_bank_id.bank_name + '_' +
            # str(retorno_obj.data) + '.pdf'

            ##
            ## Anexa os boletos em PDF ao registro da remessa
            ##
            #attachment_pool = self.pool.get('ir.attachment')
            #attachment_ids = attachment_pool.search(cr, uid, [(
            # 'res_model', '=', 'finan.retorno'), (
            # 'res_id', '=', retorno_obj.id), ('name', '=', nome_boleto)])
            ##
            ## Apaga os boletos anteriores com o mesmo nome
            ##
            #attachment_pool.unlink(cr, uid, attachment_ids)

            #dados = {
                #'datas': base64.encodestring(pdf),
                #'name': nome_boleto,
                #'datas_fname': nome_boleto,
                #'res_model': 'finan.retorno',
                #'res_id': retorno_obj.id,
                #'file_type': 'application/pdf',
            #}
            #attachment_pool.create(cr, uid, dados)

            ##
            ## Gera a remessa propriamente dita
            ##
            #remessa = Remessa()
            #remessa.tipo = 'CNAB_400'
            #remessa.boletos = lista_boletos
            #remessa.sequencia = numero_arquivo
            #remessa.data_hora = datetime.strptime(retorno_obj.data,
            # '%Y-%m-%d %H:%M:%S')

            ##
            ## Nomenclatura bradesco
            ##
            #if lista_boletos[0].banco.codigo == '237':
                #nome_retorno = 'CB' + remessa.data_hora.strftime('%d%m')
            # + str(remessa.sequencia).zfill(2) + '.txt'
            #else:
                #nome_retorno = unicode(
            # retorno_obj.carteira_id.nome).encode('utf-8') + '_retorno_' +
            # str(numero_arquivo) + '.txt'

            ##
            ## Anexa a remessa ao registro da remessa
            ##
            #attachment_pool = self.pool.get('ir.attachment')
            #attachment_ids = attachment_pool.search(cr, uid, [('res_model',
            # '=', 'finan.retorno'), ('res_id', '=', retorno_obj.id), ('name',
            # '=', nome_retorno)])
            ##
            ## Apaga os boletos anteriores com o mesmo nome
            ##
            #attachment_pool.unlink(cr, uid, attachment_ids)

            #dados = {
                #'datas': base64.encodestring(remessa.arquivo_retorno),
                #'name': nome_retorno,
                #'datas_fname': nome_retorno,
                #'res_model': 'finan.retorno',
                #'res_id': retorno_obj.id,
                #'file_type': 'text/plain',
            #}
            #attachment_pool.create(cr, uid, dados)

        #def gerar_retorno_anexo(self, cr, uid, ids, context=None):
            #for id in ids:
                #self.gerar_retorno(cr, uid, id)











