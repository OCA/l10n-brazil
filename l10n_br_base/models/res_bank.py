#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <michellstut@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResBank(models.Model):
    _inherit = 'res.bank'

    code_bc = fields.Char(
        string=u'Brazilian Bank Code',
        size=3,
        help=u'Brazilian Bank Code ex.: 001 is the code of Banco do Brasil')
