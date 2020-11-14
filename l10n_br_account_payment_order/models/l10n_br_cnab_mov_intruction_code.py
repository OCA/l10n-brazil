# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields


class L10nBrCNABMovInstructionCode(models.Model):
    _name = 'l10n_br_cnab.mov.instruction.code'
    _inherit = 'l10n_br_cnab.data.abstract'
    _description = 'CNAB Movement Instruction Code'

    comment = fields.Text(
        string='Comment'
    )
