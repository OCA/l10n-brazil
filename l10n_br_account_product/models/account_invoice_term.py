# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _

BANDEIRA_CARTAO = (
    ('01', 'Visa'),
    ('02', 'Mastercard'),
    ('03', 'American Express'),
    ('04', 'Sorocred'),
    ('05', 'Diners Club'),
    ('06', 'Elo'),
    ('07', 'Hipercard'),
    ('08', 'Aura'),
    ('09', 'Cabal'),
    ('99', 'Outros'),
)
BANDEIRA_CARTAO_DICT = dict(BANDEIRA_CARTAO)

BANDEIRA_CARTAO_VISA = '01'
BANDEIRA_CARTAO_MASTERCARD = '02'
BANDEIRA_CARTAO_AMERICAN_EXPRESS = '03'
BANDEIRA_CARTAO_SOROCRED = '04'
BANDEIRA_CARTAO_DINERS_CLUB = '05'
BANDEIRA_CARTAO_ELO = '06'
BANDEIRA_CARTAO_HIPERCARD = '07'
BANDEIRA_CARTAO_AURA = '08'
BANDEIRA_CARTAO_CABAL = '09'
BANDEIRA_CARTAO_OUTROS = '99'

INTEGRACAO_CARTAO = (
    ('1', 'Integrado'),
    ('2', 'Não integrado'),
)
INTEGRACAO_CARTAO_INTEGRADO = '1'
INTEGRACAO_CARTAO_NAO_INTEGRADO = '2'

FORMA_PAGAMENTO = (
    ('01', 'Dinheiro'),
    ('02', 'Cheque'),
    ('03', 'Cartão de crédito'),
    ('04', 'Cartão de débito'),
    ('05', 'Crédito na loja'),
    ('10', 'Vale alimentação'),
    ('11', 'Vale refeição'),
    ('12', 'Vale presente'),
    ('13', 'Vale combustível'),
    ('14', 'Duplicata mercantil'),
    ('15', 'Boleto bancário'),
    ('90', 'Sem pagamento'),
    ('99', 'Outros'),
)

FORMA_PAGAMENTO_DICT = dict(FORMA_PAGAMENTO)

FORMA_PAGAMENTO_DINHEIRO = '01'
FORMA_PAGAMENTO_CHEQUE = '02'
FORMA_PAGAMENTO_CARTAO_CREDITO = '03'
FORMA_PAGAMENTO_CARTAO_DEBITO = '04'
FORMA_PAGAMENTO_CREDITO_LOJA = '05'
FORMA_PAGAMENTO_VALE_ALIMENTACAO = '10'
FORMA_PAGAMENTO_VALE_REFEICAO = '11'
FORMA_PAGAMENTO_VALE_PRESENTE = '12'
FORMA_PAGAMENTO_VALE_COMBUSTIVEL = '13'
FORMA_PAGAMENTO_DUPLICATA_MERCANTIL = '14'
FORMA_PAGAMENTO_BOLETO = '15'
FORMA_PAGAMENTO_SEM_PAGAMENTO = '90'
FORMA_PAGAMENTO_OUTROS = '99'

FORMA_PAGAMENTO_CARTOES = (
    FORMA_PAGAMENTO_CARTAO_CREDITO,
    FORMA_PAGAMENTO_CARTAO_DEBITO,
)

IND_FORMA_PAGAMENTO = (
    ('0', 'À vista'),
    ('1', 'A prazo'),
    ('2', 'Outros/sem pagamento'),
)
IND_FORMA_PAGAMENTO_DICT = dict(IND_FORMA_PAGAMENTO)


class AccountPaymentTerm(models.Model):

    _inherit = b'account.payment.term'
    _order = 'display_name'

    @api.depends('forma_pagamento', 'name')
    def _compute_display_name(self):
        return super(AccountPaymentTerm, self)._compute_display_name()

    display_name = fields.Char(
        string='Condição da pagamento',
        store=True,
        compute='_compute_display_name',
    )
    #
    # Campos para NF-e e SPED
    #
    ind_forma_pagamento = fields.Selection(
        selection=IND_FORMA_PAGAMENTO,
        string='Indicador da Forma de Pagamento',
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
        default=FORMA_PAGAMENTO_OUTROS,
        required=True,
    )
    card_brand = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string='Bandeira do cartão',
    )
    card_integration = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string='Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Operadora do cartão',
        ondelete='restrict',
    )

    @api.multi
    def name_get(self):
        res = []

        for payment_term in self:
            display_name = ''
            if payment_term.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
                if payment_term.forma_pagamento == \
                        FORMA_PAGAMENTO_CARTAO_CREDITO:
                    display_name += '[Crédito '
                elif payment_term.forma_pagamento == \
                        FORMA_PAGAMENTO_CARTAO_DEBITO:
                    display_name += '[Débito '

                display_name += \
                    BANDEIRA_CARTAO_DICT[payment_term.card_brand]
                display_name += '] '

            elif payment_term.forma_pagamento:
                display_name += '['
                display_name += \
                    FORMA_PAGAMENTO_DICT[payment_term.forma_pagamento]
                display_name += '] '

            display_name += payment_term.name
            res.append((payment_term.id, display_name))

        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()

        if not recs:
            recs = self.search(
                [
                    ('display_name', operator, name),
                ] + args, limit=limit)
        return recs.name_get()
