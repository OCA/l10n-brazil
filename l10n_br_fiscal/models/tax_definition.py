# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .. import tools
from ..constants.fiscal import (
    FINAL_CUSTOMER,
    FISCAL_IN_OUT,
    FISCAL_OUT,
    OPERATION_STATE,
    OPERATION_STATE_DEFAULT,
)


class TaxDefinition(models.Model):
    _name = "l10n_br_fiscal.tax.definition"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Tax Definition"

    def _get_complete_name(self):
        return "{tax_group}-{tax}-{cst_code}".format(
            tax_group=self.tax_group_id.name,
            tax=self.tax_id.name,
            cst_code=self.cst_code,
        )

    @api.depends("tax_group_id", "tax_id", "cst_code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record._get_complete_name()

    @api.depends("tax_group_id", "tax_id", "cst_code")
    def name_get(self):
        result = []
        for record in self:
            name = record._get_complete_name()
            result.append((record.id, name))
        return result

    display_name = fields.Char(compute="_compute_display_name", store=True)

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT,
        string="Type",
        required=True,
        default=FISCAL_OUT,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Tax Group",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    custom_tax = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('tax_group_id', '=', tax_group_id)]",
    )

    cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST",
        readonly=True,
        domain="[('cst_type', 'in', (type_in_out, 'all')), "
        "('tax_group_id', '=', tax_group_id)]",
    )

    cst_code = fields.Char(
        string="CST Code",
        related="cst_id.code",
        readonly=True,
    )

    tax_domain = fields.Selection(
        related="tax_group_id.tax_domain",
        store=True,
        string="Tax Domain",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    is_taxed = fields.Boolean(
        string="Taxed?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    is_debit_credit = fields.Boolean(
        string="Debit/Credit?",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state_from_id = fields.Many2one(
        comodel_name="res.country.state",
        string="From State",
        domain=[("country_id.code", "=", "BR")],
    )

    state_to_ids = fields.Many2many(
        comodel_name="res.country.state",
        relation="tax_definition_state_to_rel",
        column1="tax_definition_id",
        column2="state_id",
        string="To States",
        domain=[("country_id.code", "=", "BR")],
    )

    ncms = fields.Text(
        string="NCM List",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    ncm_exception = fields.Text(
        string="NCM Exeption",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    not_in_ncms = fields.Text(
        string="Not in NCMs",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    ncm_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.ncm",
        relation="tax_definition_ncm_rel",
        column1="tax_definition_id",
        column2="ncm_id",
        readonly=True,
        string="NCMs",
    )

    cests = fields.Text(
        string="CEST List",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cest_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cest",
        relation="tax_definition_cest_rel",
        column1="tax_definition_id",
        column2="cest_id",
        readonly=True,
        string="CESTs",
    )

    nbms = fields.Text(
        string="NBM List",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    not_in_nbms = fields.Text(
        string="Not in NBMs",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    nbm_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.nbm",
        relation="tax_definition_nbm_rel",
        column1="tax_definition_id",
        column2="nbm_id",
        readonly=True,
        string="NBMs",
    )

    product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="tax_definition_product_rel",
        column1="tax_definition_id",
        column2="product_id",
        string="Products",
    )

    city_taxation_code_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.city.taxation.code",
        relation="tax_definition_city_taxation_code_rel",
        column1="tax_definition_id",
        column2="city_taxation_code_id",
        string="City Taxation Codes",
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string="Final Consumption Operation",
    )

    date_start = fields.Datetime(
        string="Start Date",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    date_end = fields.Datetime(
        string="End Date",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        selection=OPERATION_STATE,
        default=OPERATION_STATE_DEFAULT,
        index=True,
        readonly=True,
        tracking=True,
        copy=False,
    )

    ipi_guideline_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.guideline",
        string="IPI Guideline",
        domain="['|', ('cst_in_id', '=', cst_id), ('cst_out_id', '=', cst_id)]",
    )

    def _get_search_domain(self, tax_definition):
        """Create domain to be used in contraints methods"""
        domain = [
            ("id", "!=", tax_definition.id),
            ("state_from_id", "=", tax_definition.state_from_id.id),
            ("state_to_ids", "in", tax_definition.state_to_ids.ids),
            ("tax_group_id", "=", tax_definition.tax_group_id.id),
            ("tax_id", "=", tax_definition.tax_id.id),
        ]
        return domain

    def action_review(self):
        self.write({"state": "review"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_draft(self):
        self.write({"state": "draft"})

    def unlink(self):
        operations = self.filtered(lambda line: line.state == "approved")
        if operations:
            raise UserError(
                _("You cannot delete an Tax Definition which is not draft !")
            )
        return super().unlink()

    def action_search_ncms(self):
        ncm = self.env["l10n_br_fiscal.ncm"]
        for r in self:
            domain = []

            if r.ncms:
                domain += tools.domain_field_codes(r.ncms)

            if r.not_in_ncms:
                domain += tools.domain_field_codes(
                    field_codes=r.not_in_ncms, operator1="!=", operator2="not ilike"
                )

            if r.ncm_exception:
                domain += tools.domain_field_codes(
                    field_codes=r.ncm_exception, field_name="exception", code_size=2
                )

            if domain:
                r.ncm_ids = ncm.search(domain)
            else:
                r.ncm_ids = False

    def action_search_cests(self):
        cest = self.env["l10n_br_fiscal.cest"]
        for r in self:
            domain = []

            if r.cests:
                domain += tools.domain_field_codes(r.cests, code_size=7)

            if domain:
                r.cest_ids = cest.search(domain)
            else:
                r.cest_ids = False

    def action_search_nbms(self):
        nbm = self.env["l10n_br_fiscal.nbm"]
        for r in self:
            domain = []

            if r.nbms:
                domain += tools.domain_field_codes(r.nbms, code_size=10)

            if r.not_in_nbms:
                domain += tools.domain_field_codes(
                    field_codes=r.not_in_nbms,
                    operator1="!=",
                    operator2="not ilike",
                    code_size=10,
                )

            if domain:
                r.nbm_ids = nbm.search(domain)
            else:
                r.nbm_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        create_super = super().create(vals_list)
        ncm_fields_list = ("ncms", "not_in_ncms", "ncm_exception")
        for index, values in enumerate(vals_list):
            if set(ncm_fields_list).intersection(values.keys()):
                create_super[index].with_context(do_not_write=True).action_search_ncms()
            if "cests" in values.keys():
                create_super[index].with_context(
                    do_not_write=True
                ).action_search_cests()
            if "nbms" in values.keys():
                create_super[index].with_context(do_not_write=True).action_search_nbms()
        return create_super

    def write(self, values):
        write_super = super().write(values)
        ncm_fields_list = ("ncms", "not_in_ncms", "ncm_exception")
        do_not_write = self.env.context.get("do_not_write")
        if set(ncm_fields_list).intersection(values.keys()) and not do_not_write:
            self.with_context(do_not_write=True).action_search_ncms()
        if "cests" in values.keys() and not do_not_write:
            self.with_context(do_not_write=True).action_search_cests()
        if "nbms" in values.keys() and not do_not_write:
            self.with_context(do_not_write=True).action_search_nbms()
        return write_super

    def map_tax_definition(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        nbs=None,
        cest=None,
        city_taxation_code=None,
    ):
        if not ncm:
            ncm = product.ncm_id

        if not nbm:
            nbm = product.nbm_id

        if not cest:
            cest = product.cest_id

        domain = [
            ("id", "in", self.ids),
            "|",
            ("state_to_ids", "=", False),
            ("state_to_ids", "=", partner.state_id.id),
            "|",
            ("ncm_ids", "=", False),
            ("ncm_ids", "=", ncm.id),
            "|",
            ("nbm_ids", "=", False),
            ("nbm_ids", "=", nbm.id),
            "|",
            ("cest_ids", "=", False),
            ("cest_ids", "=", cest.id),
            "|",
            ("city_taxation_code_ids", "=", False),
            ("city_taxation_code_ids", "=", city_taxation_code.id),
            "|",
            ("product_ids", "=", False),
            ("product_ids", "=", product.id),
        ]

        return self.search(domain)

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
