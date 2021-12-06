# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class DocumentRelated(models.Model):
    _inherit = "l10n_br_fiscal.document.related"

    pos_related_id = fields.Many2one(
        comodel_name="pos.order",
        string="POS Fiscal Document",
        ondelete="cascade",
        index=True,
    )

    @api.onchange("pos_related_id")
    def onchange_pos_related_id(self):
        if self.pos_related_id:
            # self.document_type = 'sat' # FIXME
            self.document_key = self.pos_related_id.chave_cfe[3:]
            self.document_date = self.pos_related_id.date_order[:10]
