# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *

from pybrasil.data import parse_datetime, hoje, formata_data
from pybrasil.valor.decimal import Decimal as D
#from numpy import base_repr
from pybrasil.febraban import *
from pybrasil.valor import formata_valor, valor_por_extenso_unidade
from dateutil.relativedelta import relativedelta


class FinanCarteira(SpedBase, models.Model):
    _name = b'finan.carteira'
    _description = 'Carteira de Boletos'
    _rec_name = 'nome'
    #_order = 'nome'

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        #store=True,
        #index=True,
    )
    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Conta bancária',
        required=True,
        index=True,
        domain="[('banco', '!=', '000')]",  # Carteiras não podem usar o
                                            # banco interno
    )
    #
    # Alguns bancos usam o leiaute de outro nas remessas
    #
    banco = fields.Selection(
        selection=FINAN_BANCO_CHEQUE_BOLETO,
    )

    #
    # Os campos abaixo têm nomes diferentes conforme o banco,
    # e nem todo banco usa todos os campos, é uma zona!
    #
    carteira = fields.Char(
        string='Carteira',
        size=10,
        required=True,
    )
    beneficiario = fields.Char(
        string='Beneficiário',
        size=20,
        required=True,
    )
    beneficiario_digito = fields.Char(
        string='Dígito do beneficiário',
        size=1,
        required=True,
    )
    sacador_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Sacador avalista',
        ondelete='restrict',
    )

    #
    # Variam conforme o banco
    #
    convenio = fields.Char(
        string='Convênio',
        size=10,
    )
    modalidade = fields.Char(
        string='Modalidade',
        size=10,
    )

    #
    # Dependem de negociação com o banco (entrega via correio)
    #
    banco_emite = fields.Boolean(
        string='Emissão (nosso número) pelo banco?',
    )
    banco_entrega = fields.Boolean(
        string='Entrega pelo banco?',
    )

    #
    # Juros e multa
    #
    al_juros = fields.Monetary(
        string='Taxa de juros (mensal)',
        currency_field='currency_aliquota_id'
    )
    al_multa = fields.Monetary(
        string='Percentual de multa',
        currency_field='currency_aliquota_id'
    )

    #
    # Protesto e outros controles por dias
    #
    dias_protesto = fields.Integer(
        string='Dias para protesto',
    )
    dias_nao_recebimento = fields.Integer(
        string='Dias para não recebimento',
    )
    dias_negativacao = fields.Integer(
        string='Dias para negativação',
    )

    #
    # Controle da numeração dos boletos e arquivos,
    # não podemos usar o sequence aqui, pois alguns bancos
    # usam uma numeração imensa, alguns com uma quantidade de dígitos
    # específica, às vezes até 15 dígitos!
    #
    proximo_nosso_numero = fields.Char(
        string='Próximo nosso número',
        size=20,
        required=True,
        default='1',
    )
    proxima_remessa = fields.Integer(
        string='Próxima remessa',
        required=True,
        default=1,
    )

    @api.depends('banco_id', 'banco_id.banco', 'banco_id.titular_id',
                 'carteira',
                 'beneficiario', 'beneficiario_digito')
    def _compute_nome(self):
        for carteira in self:
            nome = carteira.banco_id.nome.split('/')[0].strip()
            nome += ' / '
            nome += carteira.carteira
            nome += ' / '
            nome += carteira.beneficiario
            nome += '-'
            nome += carteira.beneficiario_digito

            if not self.env.context.get('banco_sem_titular'):
                nome += ' / '
                nome += carteira.banco_id.titular_id.name_get()[0][1]

            carteira.nome = nome

    def gera_boleto(self, divida):
        self.ensure_one()

        if divida.tipo != FINAN_DIVIDA_A_RECEBER:
            return

        if not divida.carteira_id:
            return

        #
        # Pegamos a carteira com o usuário admin, vejam comentários mais abaixo
        #
        carteira = \
            self.env['finan.carteira'].sudo().browse(divida.carteira_id.id)

        boleto = Boleto()

        if carteira.banco:
            boleto.banco = BANCO_CODIGO[carteira.banco]
        else:
            boleto.banco = BANCO_CODIGO[carteira.banco_id.banco]

        #
        # Dados da carteira
        #
        boleto.banco.carteira = carteira.carteira
        boleto.banco.modalidade = carteira.modalidade

        boleto.beneficiario.agencia.numero = carteira.banco_id.agencia or ''
        boleto.beneficiario.agencia.digito = \
            carteira.banco_id.agencia_digito or ''
        boleto.beneficiario.conta.numero = carteira.banco_id.conta or ''
        boleto.beneficiario.conta.digito = carteira.banco_id.conta_digito or ''
        boleto.beneficiario.banco.convenio = carteira.convenio or ''
        boleto.beneficiario.codigo.numero = carteira.beneficiario or ''
        boleto.beneficiario.codigo.digito = carteira.beneficiario_digito or ''

        #
        # Dados do beneficiário
        #
        beneficiario = carteira.banco_id.titular_id
        boleto.beneficiario.nome = beneficiario.razao_social
        boleto.beneficiario.cnpj_cpf = beneficiario.cnpj_cpf
        boleto.beneficiario.endereco = beneficiario.endereco
        boleto.beneficiario.numero = beneficiario.numero
        boleto.beneficiario.complemento = beneficiario.complemento or ''
        boleto.beneficiario.bairro = beneficiario.bairro
        boleto.beneficiario.cidade = beneficiario.cidade
        boleto.beneficiario.estado = beneficiario.estado
        boleto.beneficiario.cep = beneficiario.cep

        #
        # Dados do sacador
        #
        if carteira.sacador_id:
            sacador = carteira.sacador_id
            boleto.sacador.nome = sacador.razao_social
            boleto.sacador.cnpj_cpf = sacador.cnpj_cpf
            boleto.sacador.endereco = sacador.endereco
            boleto.sacador.numero = sacador.numero
            boleto.sacador.complemento = sacador.complemento or ''
            boleto.sacador.bairro = sacador.bairro
            boleto.sacador.cidade = sacador.cidade
            boleto.sacador.estado = sacador.estado
            boleto.sacador.cep = sacador.cep

        #
        # Dados do pagador/cliente
        #
        pagador = divida.participante_id
        boleto.pagador.nome = pagador.razao_social
        boleto.pagador.cnpj_cpf = pagador.cnpj_cpf
        boleto.pagador.endereco = pagador.endereco
        boleto.pagador.numero = pagador.numero
        boleto.pagador.complemento = pagador.complemento or ''
        boleto.pagador.bairro = pagador.bairro
        boleto.pagador.cidade = pagador.cidade
        boleto.pagador.estado = pagador.estado
        boleto.pagador.cep = pagador.cep

        #
        # Dados do documento
        #
        # A identificação é o próprio id da dívida, para simplificar o
        # tratamento do retorno depois
        #
        #boleto.identificacao = 'ID' + base_repr(divida.id, 36)
        boleto.identificacao = 'N' + str(divida.id)
        boleto.data_vencimento = divida.data_vencimento
        boleto.data_processamento = hoje()

        boleto.documento.numero = divida.numero
        boleto.documento.data = divida.data_documento
        boleto.documento.valor = D(divida.vr_documento or 0)
        boleto.documento.especie = 'DM'
        boleto.documento.numero_original = divida.numero

        #
        # Juros e multa; a multa em geral é 2% e os juros 1% ao mês, mas
        # a maioria dos bancos pede que se informe os juros diários,
        # exceto o SICOOB, que exige que os juros sejam informados por mês
        #
        boleto.instrucoes = []
        if carteira.al_multa:
            boleto.data_multa = boleto.data_vencimento + relativedelta(days=1)
            boleto.percentual_multa = D(carteira.al_multa)
            boleto.valor_multa = \
                boleto.documento.valor * boleto.percentual_multa / 100
            boleto.valor_multa = boleto.valor_multa.quantize(D('0.01'))
            mensagem_multa = \
                'A partir de ' + formata_data(boleto.data_multa) + \
                ' cobrar R$ ' + formata_valor(boleto.valor_multa) + \
                ' (' + valor_por_extenso_unidade(boleto.valor_multa) + \
                ') de multa;'
            boleto.instrucoes.append(mensagem_multa)

        if carteira.al_juros:
            boleto.data_multa = boleto.data_vencimento + relativedelta(days=1)
            boleto.percentual_juros = D(carteira.al_juros)
            boleto.valor_juros = \
                boleto.documento.valor * boleto.percentual_juros / 100

            if carteira.banco != FINAN_BANCO_SICOOB:
                boleto.valor_juros /= 30  # Para os juros serem diários

            boleto.valor_juros = boleto.valor_juros.quantize(D('0.01'))
            mensagem_juros = \
                'A partir de ' + formata_data(boleto.data_juros) + \
                ' cobrar R$ ' + formata_valor(boleto.valor_juros) + \
                ' (' + valor_por_extenso_unidade(boleto.valor_juros)

            if carteira.banco != FINAN_BANCO_SICOOB:
                mensagem_juros += ') de juros de mora por dia;'
            else:
                mensagem_juros += ') de juros de mora por mês;'

            boleto.instrucoes.append(mensagem_juros)

        #
        # Por fim, tratamos o nosso número
        #
        if divida.nosso_numero and divida.nosso_numero != '0':
            boleto.nosso_numero = divida.nosso_numero

        #
        # Quando o banco emite o boleto, o nosso número é determinado pelo
        # banco somente depois da remessa/registro junto ao banco
        #
        elif not carteira.banco_emite:
            proximo_nosso_numero = D(carteira.proximo_nosso_numero)
            proximo_nosso_numero = proximo_nosso_numero.quantize(D(1))
            divida.nosso_numero = str(proximo_nosso_numero)
            boleto.nosso_numero = divida.nosso_numero
            #
            # Aqui podemos salvar o próximo nosso número tranquilamente, pois
            # a carteira aqui está usando o usuário admin, então, não corremos
            # riscos do usuário não ter permissão de atualizar o próximo
            # nosso número, coisa que em geral somente o gerente financeiro
            # deveria poder fazer
            #
            carteira.proximo_nosso_numero = str(proximo_nosso_numero + 1)

        #
        # Por fim, se por acaso a dívida estiver provisória, se emitimos um
        # boleto, tornamos a dívida efetiva
        #
        if divida.provisorio:
            divida.provisorio = False

        return boleto
