# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class L10nBrCnabFileSufixSequence(models.Model):
    _name = 'l10n_br_cnab_file_sufix.sequence'

    code = fields.Char(u'Código')
    name = fields.Char(u'Nome')
    internal_sequence_id = fields.Many2one(
        'ir.sequence', u'Sequência Interna')
    parent_payment_mode_suf = fields.Many2one(
        'payment.mode', "Conta de exportação", select=True)
