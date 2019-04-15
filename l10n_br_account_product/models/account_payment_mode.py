# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    type_nf_payment = fields.Selection(
        selection=[('01', u'01 - Dinheiro'),
                   ('02', u'02 - Cheque'),
                   ('03', u'03 - Cartão de Crédito'),
                   ('04', u'04 - Cartão de Débito'),
                   ('06', u'05 - Crédito Loja'),
                   ('10', u'10 - Vale Alimentação'),
                   ('11', u'11 - Vale Refeição'),
                   ('12', u'12 - Vale Presente'),
                   ('13', u'13 - Vale Combustível'),
                   ('14', u'14 - Duplicata Mercantil'),
                   ('15', u'15 - Boleto Bancário'),
                   ('90', u'90 - Sem pagamento'),
                   ('99', u'99 - Outros')],
        string='Tipo de Pagamento da NF',
        required=True,
        default='99',
        help=u'Obrigatório o preenchimento do Grupo Informações de Pagamento'
             u' para NF-e e NFC-e. Para as notas com finalidade de Ajuste'
             u' ou Devolução o campo Forma de Pagamento deve ser preenchido'
             u' com 90 - Sem Pagamento.')
