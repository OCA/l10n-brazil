# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import *
from odoo.addons.finan.constantes import FINAN_DIVIDA_A_RECEBER
from odoo.exceptions import ValidationError, UserError


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    finan_documento_id = fields.Many2one(
        comodel_name='finan.documento',
        string='Tipo de documento',
        ondelete='restrict',
    )
    finan_conta_id = fields.Many2one(
        comodel_name='finan.conta',
        string='Conta financeira',
        ondelete='restrict',
        domain=[('tipo', '=', 'A')],
    )
    finan_lancamento_ids = fields.One2many(
        comodel_name='finan.lancamento',
        inverse_name='sped_documento_id',
        string='Lançamentos Financeiros',
        copy=False,
    )

    @api.onchange('condicao_pagamento_id')
    def onchange_condicao_pagamento_id(self):
        # para que apenas apareça carteira quando for tipo boleto
        self.forma_pagamento = \
            self.condicao_pagamento_id.forma_pagamento_id.forma_pagamento

        # Setar carteira padrao caso a condicao de pagamento for tipo boleto
        if self.forma_pagamento == '15':
            self.carteira_id = \
                self.env['sped.empresa']._empresa_ativa().carteira_id
        else:
            self.carteira_id = False

        # apenas carteira padrão e permitida pra exibir
        ids = []
        for carteira in self.env.user.company_id.sped_empresa_id.carteira_ids:
            ids.append(carteira.ids)
        ids.append(self.env.user.company_id.sped_empresa_id.carteira_id.id)
        return {'domain': {'carteira_id': [('id', 'in', ids)]}}

    carteira_id = fields.Many2one(
        string='Carteira Padrão',
        comodel_name='finan.carteira',
        help='Carteira para geração do boleto',
    )

    anexos = fields.Boolean(
        string='Anexos Gerados',
        readonly=True,
    )

    forma_pagamento_id = fields.Many2one(
       comodel_name = 'finan.forma.pagamento',
       string = 'Forma de pagamento',
       related = 'condicao_pagamento_id.forma_pagamento_id',
       ondelete = 'restrict',
    )
    forma_pagamento = fields.Selection(
       selection = FORMA_PAGAMENTO,
       string = 'Forma de pagamento fiscal',
       related = 'forma_pagamento_id.forma_pagamento',
    )

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def _onchange_operacao_id(self):
        res = super(SpedDocumento, self)._onchange_operacao_id()

        if not self.operacao_id:
            return res

        if self.operacao_id.finan_documento_id:
            res['value']['finan_documento_id'] = \
                self.operacao_id.finan_documento_id.id

        if self.operacao_id.finan_conta_id:
            res['value']['finan_conta_id'] = \
                self.operacao_id.finan_conta_id.id

        return res

    def exclui_finan_lancamento(self):
        for documento in self:
            #
            # Para excluir os lançamentos vinculados à nota, precisamos
            # primeiro quebrar o vínculo de segurança
            #
            for lancamento in documento.finan_lancamento_ids:
                lancamento.sped_documento_duplicata_id = False
                lancamento.sped_documento_id = False
                lancamento.referencia_id = False
                lancamento.unlink()

    def gera_finan_lancamento(self):
        for documento in self:
            if documento.situacao_fiscal not in \
                    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO:
                continue

            if documento.emissao == TIPO_EMISSAO_PROPRIA and \
                documento.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                continue

            if not documento.finan_conta_id:
                operacao_id = self._busca_operacao()

                try:
                    documento.operacao_id = operacao_id.id

                    try:
                        documento.finan_conta_id = operacao_id.finan_conta_id
                        documento.finan_documento_id = \
                            operacao_id.finan_documento_id
                    except:
                        raise UserError(
                            _("É necessário cadastrar uma Conta na Operação "
                              "para os CFOPs dos itens importados.")
                        )
                except:
                    raise UserError(
                        _("É preciso definir uma operação com uma conta para "
                          "os CFOPs dos itens importados")
                    )

        documento.duplicata_ids.gera_lancamento_financeiro()

    def _busca_operacao(self):
        '''
        Este método busca, a partir de um sped.documento, uma operação cujo
        CFOP contenha o CFOP dos itens deste sped.documento.

        :return: Um objeto do tipo 'sped.operacao' caso seja encontrado.
        'False' caso contrário
        '''

        result = False

        #Lista de CFOPs dos items do sped.documento
        cfop_item_ids = self.item_ids.mapped('cfop_original_id.codigo')

        if len(cfop_item_ids):

            #Os items de operações que contenham os elementos da lista de cfops
            operacao_item_ids = self.env['sped.operacao.item'].search([
                ('cfop_id.codigo', 'in', cfop_item_ids),
            ])

            #As Operações referentes a estes itens de operações
            operacao_ids = operacao_item_ids.mapped('operacao_id')

            #Restringe as operações que tenham configuração de empresa para
            # apenas a empresa definida no sped.documento (ou nenhuma empresa)
            operacao_ids -= self.env['sped.operacao'].search([
                ('empresa_id', '!=', self.empresa_id.id),
            ])

            if len(operacao_ids):
                result = operacao_ids

        return result

    def regera_finan_lancamento(self):
        for documento in self:
            documento.exclui_finan_lancamento()
            documento.gera_finan_lancamento()

    def executa_depois_autorizar(self):
        super(SpedDocumento, self).executa_depois_autorizar()

    def executa_depois_cancelar(self):
        super(SpedDocumento, self).executa_depois_cancelar()
        self.exclui_finan_lancamento()

    def executa_depois_inutilizar(self):
        super(SpedDocumento, self).executa_depois_inutilizar()
        self.exclui_finan_lancamento()

    def executa_depois_denegar(self):
        super(SpedDocumento, self).executa_depois_denegar()
        self.exclui_finan_lancamento()

    def executa_depois_create(self, result, dados):
        result = \
            super(SpedDocumento, self).executa_depois_create(result, dados)

        # ativar onchange que cria duplicata
        # O documento ainda nao esta pronto para gerar o financeiro,
        # pois esta faltando uma série de informações
        for documento in result:
            documento.gera_finan_lancamento()

        return result

    def _check_regerar_financeiro(self, dados):
        """
        Validação para identificar se o financeiro deve ser refeito
        :param dados: dict com campos que serão alterados no write
        :return: 
        """
        # Lista de campos do sped.documento que se forem alterados devera ser
        # relançado os movimentos financeiros
        campos_afetam_financeiro = [
            'duplicata_ids', 'vr_nf', 'vr_fatura', 'condicao_pagamento_id',
            'carteira_id', 'item_ids', 'participante_id', 'ind_forma_pagamento',
        ]

        for campo in dados:
            if campo in campos_afetam_financeiro:
                return True
        return False

    def executa_antes_write(self, dados):
        dados = super(SpedDocumento, self).executa_antes_write(dados)

        for documento in self:
            if documento._check_regerar_financeiro(dados):
                documento.exclui_finan_lancamento()

        return dados

    def executa_depois_write(self, result, dados):
        result = super(SpedDocumento, self).executa_depois_write(result, dados)

        for documento in self:
            if documento._check_regerar_financeiro(dados):
                documento.gera_finan_lancamento()

        return result

    def executa_antes_unlink(self):
        super(SpedDocumento, self).executa_antes_unlink()

        for documento in self:
            documento.exclui_finan_lancamento()

    @api.multi
    def gera_boleto_documento_fiscal(self):
        for documento_id in self:
            forma_id = documento_id.condicao_pagamento_id.forma_pagamento_id
            boleto = forma_id.forma_pagamento == '15'

            if documento_id.condicao_pagamento_id and boleto:

                for lancamento_id in documento_id.finan_lancamento_ids:

                    # valida se esta definido a carteira de pagamento de
                    # boletos no lancamento financeiro
                    if not lancamento_id.carteira_id:

                        # Verifica se tem uma carteira padrao na empresa
                        if self.env.user.company_id.sped_empresa_id.carteira_id:
                            # se estiver configura carteira padrao, atribui ao
                            # lancamento e ao documento fiscal a carteira
                            carteira_padrao = \
                                self.env.user.company_id.sped_empresa_id.carteira_id
                            lancamento_id.carteira_id = carteira_padrao
                            documento_id.carteira_id = carteira_padrao
                        else:
                            raise ValidationError(
                                'Não foi encontrado a carteira padrão para '
                                'boletos definido pela empresa.\n Acesse o '
                                'cadastro da empresa e na aba comercial, '
                                'configure a carteira padrão.')

                    boleto = lancamento_id.gera_boleto()
                    documento_id._grava_anexo(boleto.nome, boleto.pdf)
            # documento_id.anexos = True
