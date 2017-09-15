# -*- coding: utf-8 -*-
# #############################################################################
#
#
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
#    @author Fernando Marcato Rodrigues
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


# ESTADOS_CNAB = [
#     ('draft', u'Inicial'),
#     ('added', u'Adicionada à ordem de pagamento'),
#     ('exported', u'Exportada'),
#     ('accepted', u'Aceita'),
#     ('not_accepted', u'Não aceita pelo banco'), # importar novamente
# ]


class AccounMoveLine(models.Model):
    _inherit = "account.move.line"
    #
    # state_cnab = fields.Selection(
    #     ESTADOS_CNAB, u'Estados CNAB', default='draft')

    is_cnab_rejected = fields.Boolean(
        u'Pode ser exportada novamente', default=False,
        help='Marque esse campo para indicar um título que pode ser '
             'exportado novamente pelo CNAB')
    cnab_rejected_code = fields.Char(u'Rejeição')
    # transaction_ref = fields.char('Transaction Ref.',
    #                               select=True,
    #                               store=True,
    #                               related='name')
