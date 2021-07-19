# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import CEST_SEGMENT
from ..tools import misc


class Cest(models.Model):
    _name = "l10n_br_fiscal.cest"
    _inherit = "l10n_br_fiscal.data.product.abstract"
    _description = "CEST"

    code = fields.Char(size=9)

    code_unmasked = fields.Char(size=7)

    name = fields.Text(string="Name", required=True, index=True)

    item = fields.Char(string="Item", required=True)

    segment = fields.Selection(selection=CEST_SEGMENT, string="Segment", required=True)

    product_tmpl_ids = fields.One2many(inverse_name="cest_id")

    ncms = fields.Char(string="NCM")

    ncm_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.ncm",
        relation="fiscal_cest_ncm_rel",
        column1="cest_id",
        column2="ncm_id",
        readonly=True,
        string="NCMs",
    )

    tax_definition_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        relation="tax_definition_cest_rel",
        column1="cest_id",
        column2="tax_definition_id",
        readonly=True,
        string="Tax Definition",
    )

    @api.model
    def create(self, values):
        create_super = super(Cest, self).create(values)
        if "ncms" in values.keys():
            create_super.with_context(do_not_write=True).action_search_ncms()
        return create_super

    def write(self, values):
        write_super = super(Cest, self).write(values)
        do_not_write = self.env.context.get("do_not_write")
        if "ncms" in values.keys() and not do_not_write:
            self.with_context(do_not_write=True).action_search_ncms()
        return write_super

    def action_search_ncms(self):
        ncm = self.env["l10n_br_fiscal.ncm"]
        for r in self:
            if r.ncms:
                domain = misc.domain_field_codes(field_codes=r.ncms)
                r.ncm_ids = ncm.search(domain)
