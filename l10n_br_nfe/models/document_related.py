# Copyright (C) 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from erpbrasil.base import fiscal


class DocumentRelated(models.Model):
    _name = 'l10n_br_fiscal.document.related'
    _inherit = [_name, 'nfe.40.nfref']

    nfe40_NFref_ide_id = fields.Many2one(
        related='fiscal_document_id',
    )

    nfe40_choice4 = fields.Selection(
        compute='_compute_choice4',
        store=True,
    )

    @api.depends('document_type_id')
    def _compute_choice4(self):
        for record in self:
            if record.document_type_id.code == '55':
                record.nfe40_choice4 = 'nfe40_refNFe'
            elif record.document_type_id.code == '57':
                record.nfe40_choice4 = 'nfe40_refCTe'
            else:
                raise NotImplementedError

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        xsd_fields = [self.nfe40_choice4]
        return super()._export_fields(xsd_fields, class_obj, export_dict)
