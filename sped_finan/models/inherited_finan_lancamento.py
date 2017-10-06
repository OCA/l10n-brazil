# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from openerp.addons.l10n_br_base.models.sped_base import SpedBase


class FinanLancamento(SpedBase, models.Model):
    _inherit = 'finan.lancamento'

    referencia_id = fields.Reference(
        selection_add=[('sped.documento', 'Documento Fiscal')],
    )
    sped_documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
        ondelete='restrict',
    )
    sped_documento_duplicata_id = fields.Many2one(
        comodel_name='sped.documento.duplicata',
        string='Duplicata do Documento Fiscal',
        ondelete='restrict',
    )
