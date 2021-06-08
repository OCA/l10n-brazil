# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..tools import misc


class Nbm(models.Model):
    _name = "l10n_br_fiscal.nbm"
    _inherit = "l10n_br_fiscal.data.product.abstract"
    _description = "NBM"

    code = fields.Char(size=12)

    code_unmasked = fields.Char(size=10)

    name = fields.Text(string="Name", required=True, index=True)

    product_tmpl_ids = fields.One2many(inverse_name="nbm_id")

    ncms = fields.Char(string="NCM")

    ncm_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.ncm",
        relation="fiscal_nbm_ncm_rel",
        column1="nbm_id",
        column2="ncm_id",
        readonly=True,
        string="NCMs",
    )

    @api.model
    def create(self, values):
        create_super = super(Nbm, self).create(values)
        if "ncms" in values.keys():
            create_super.with_context(do_not_write=True).action_search_ncms()
        return create_super

    def write(self, values):
        write_super = super(Nbm, self).write(values)
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
