# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import (
    FISCAL_IN_OUT,
    FISCAL_OUT,
    TAX_DOMAIN
)


class TaxDefinition(models.Model):
    _name = "l10n_br_fiscal.tax.definition"
    _description = "Tax Definition"

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT,
        string="Type",
        required=True,
        default=FISCAL_OUT)

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Tax Group")

    custom_tax = fields.Boolean(
        string="Custom Tax")

    tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        domain="[('tax_group_id', '=', tax_group_id)]",
        string="Tax")

    cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        domain="[('cst_type', 'in', (type_in_out, 'all')),"
        "('tax_domain', '=', tax_domain)]",
        string="CST")

    cst_code = fields.Char(
        string="CST Code",
        related="cst_id.code")

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        related="tax_group_id.tax_domain",
        store=True,
        string="Tax Domain")

    is_taxed = fields.Boolean(
        string="Taxed?")

    is_debit_credit = fields.Boolean(
        string="Debit/Credit?")

    tax_retention = fields.Boolean(
        string="Tax Retention?")

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company")

    ncms = fields.Char(string="NCM")

    ncm_exception = fields.Char(string="NCM Exeption")

    not_in_ncms = fields.Char(string="Not in NCM")

    ncm_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.ncm",
        relation="tax_definition_ncm_rel",
        colunm1="tax_definition_id",
        colunm2="ncm_id",
        compute="_compute_ncms",
        store=True,
        readonly=True,
        string="NCMs")

    cests = fields.Char(string="CEST")

    cest_ids = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        relation="tax_definition_cest_rel",
        colunm1="tax_definition_id",
        colunm2="ncm_id",
        compute="_compute_cests",
        store=True,
        readonly=True,
        string="CESTs")

    @api.depends("ncms")
    def _compute_ncms(self):
        ncm = self.env["l10n_br_fiscal.ncm"]
        domain = False
        for r in self:
            # Clear Field
            domain = False
            r.ncm_ids = False
            if r.ncms:
                ncms = r.ncms.split(";")
                domain = ["|"] * (len(ncms) - 1)
                domain += [("code_unmasked", "=", n) for n in ncms if len(n) == 8]
                domain += [
                    ("code_unmasked", "=ilike", n + "%") for n in ncms if len(n) < 8
                ]

            if r.not_in_ncms:
                not_in_ncms = r.not_in_ncms.split(";")
                domain += [
                    ("code_unmasked", "=", n) for n in not_in_ncms if len(n) == 8
                ]

                domain += [
                    ("code_unmasked", "not ilike", n + "%")
                    for n in not_in_ncms
                    if len(n) < 8
                ]

            if r.ncm_exception:
                ncm_exception = r.ncm_exception.split(";")
                domain += [("exception", "=", n) for n in ncm_exception]

            if domain:
                r.ncm_ids = ncm.search(domain)

    @api.depends("cests")
    def _compute_cests(self):
        cest = self.env["l10n_br_fiscal.cest"]
        domain = False
        for r in self:
            # Clear Field
            domain = False
            r.cest_ids = False
            if r.cests:
                cests = r.cests.split(";")
                domain = ["|"] * (len(cests) - 1)
                domain += [("code_unmasked", "=", n) for n in cests if len(n) == 7]
                domain += [
                    ("code_unmasked", "=ilike", n + "%") for n in cests if len(n) < 7
                ]

            if domain:
                r.cest_ids = cest.search(domain)

    @api.onchange("is_taxed")
    def _onchange_tribute(self):
        if not self.is_taxed:
            self.is_debit_credit = False
        else:
            self.is_debit_credit = True

    @api.onchange("custom_tax")
    def _onchange_custom_tax(self):
        if not self.custom_tax:
            self.tax_id = False
            self.cst_id = False

    @api.onchange("tax_id")
    def _onchange_tax_id(self):
        if self.tax_id:
            if self.type_in_out == FISCAL_OUT:
                self.cst_id = self.tax_id.cst_out_id
            else:
                self.cst_id = self.tax_id.cst_in_id
