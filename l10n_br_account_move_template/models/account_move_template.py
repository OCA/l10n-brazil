# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models

OPERATION_NATURE = [
    ('venda', u'Venda'),
    ('revenda', u'Revenda'),

]

OPERATION_POSITION = [
    ('interestadual', u'Interestadual'),
    ('dentro_estado', u'Dentro do estado'),
    ('exportacao', u'Exportação'),

]

PRODUCT_ORIGIN = [
    ('0', u'0 - Nacional, exceto as indicadas nos códigos 3 a 5'),
    ('1', u'1 - Estrangeira - Importação direta, exceto a indicada no código'
     ' 6'),
    ('2', u'2 - Estrangeira - Adquirida no mercado interno, exceto a indicada'
     u' no código 7'),
    ('3', u'3 - Nacional, mercadoria ou bem com Conteúdo de Importação'
     ' superior a 40% (quarenta por cento)'),
    ('4', u'4 - Nacional, cuja produção tenha sido feita em conformidade com'
     u' os processos produtivos básicos de que tratam o Decreto-Lei nº 288/67,'
     u' e as Leis nºs 8.248/91, 8.387/91, 10.176/01 e 11.484/07'),
    ('5', u'5 - Nacional, mercadoria ou bem com Conteúdo de Importação'
     u' inferior ou igual a 40% (quarenta por cento)'),
    ('6', u'6 - Estrangeira - Importação direta, sem similar nacional,'
     u' constante em lista de Resolução CAMEX'),
    ('7', u'7 - Estrangeira - Adquirida no mercado interno, sem similar'
     u' nacional, constante em lista de Resolução CAMEX'),
    ('8', u'8 - Nacional, mercadoria ou bem com Conteúdo de Importação'
     u' superior a 70%')
]

TERM = [
    ('curto', 'Curto prazo'),
    ('longo', 'Longo prazo')
]

OPERATION_PURPOSE = [
    ('operacional', u'Operacional'),
    ('financeiro', u'Financeiro'),
]

MOVE_TYPE = [
    ('receita', 'Receita'),
]


class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'

    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string=u'Tipo do documento'
    )
    # TODO: verificar origem desse campo
    account_type = fields.Many2one(
        comodel_name='account.account.type', string=u'Tipo de conta'
    )
    operation_nature = fields.Selection(selection=OPERATION_NATURE)
    operation_position = fields.Selection(selection=OPERATION_POSITION)
    # TODO: verificar se sera criado modelo para o tipo de produto
    product_type = fields.Char()
    product_origin = fields.Selection(selection=PRODUCT_ORIGIN)
    term = fields.Selection(selection=TERM)
    # TODO: qual a melhor forma de estruturar?
    # operation_purpose = fields.Selection(selection=OPERATION_PURPOSE)
    account_move_type = fields.Selection(selection=MOVE_TYPE)
    credit_account_id = fields.Many2one(
        comodel_name='account.account', string=u'Conta de credito'
    )
    debit_account_id = fields.Many2one(
        comodel_name='account.account', string=u'Conta de debito'
    )
    debit_compensation_account_id = fields.Many2one(
        comodel_name='account.account', string=u'Conta de compensaçao de '
                                                u'debito'
    )

    # def _map_tax_domain(self, **kwargs):
    #     domain = []
    #     for key, value in kwargs.iteritems():
    #         domain.append((str(key), '=', str(value)))
    #     return domain

    def _map_invoice_domain(self, move_line):
        domain = []
        #
        invoice = self.env['account.invoice'].browse(
            move_line.get('invoice_id'))
        company_id = invoice.company_id.id
        fiscal_document_id = invoice.fiscal_document_id.id
        account_type = invoice.account_id.user_type.id
        # operation_nature
        # operation_position
        # product_type
        # product_origin
        # term
        # account_move_type
        return domain

    def map_account(self, move_line):
        """ Parametros da tabela de decisão:
         - company_id, document_type_id,
                    account_type, operation_nature,
                    operation_position, product_type, product_origin, term,
                    operation_purpose, account_move_type
        :return: o objeto account.account
        """
        if move_line.get('invl_id'):
            domain = self._map_invoice_domain(move_line)
        elif move_line.get('tax_code'):
            domain = self._map_tax_domain(move_line)
        else:
            return move_line

        # rule = self.search(domain)
        rule = False

        if rule:
            return move_line.update({'account_id': rule.debit_account_id.id or
                                                   rule.credit_account_id.id})
        else:
            return move_line
