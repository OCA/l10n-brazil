#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
#    Akretion
#    Copyright (C) Akretion (<http://www.akretion.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal import cnpj_cpf
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class Company(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "format.address.mixin"]

    @api.multi
    def _compute_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """

        for c in self:
            c.legal_name = c.partner_id.legal_name
            c.cnpj_cpf = c.partner_id.cnpj_cpf
            c.street_number = c.partner_id.street_number
            c.district = c.partner_id.district
            c.city_id = c.partner_id.city_id
            c.inscr_est = c.partner_id.inscr_est
            c.inscr_mun = c.partner_id.inscr_mun
            c.suframa = c.partner_id.suframa
            state_tax_number_ids = self.env["state.tax.numbers"]
            for state_tax_number in c.partner_id.state_tax_number_ids:
                state_tax_number_ids |= state_tax_number
            c.state_tax_number_ids = state_tax_number_ids

    def _inverse_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.legal_name = company.legal_name

    def _inverse_district(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.district = company.district

    def _inverse_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.cnpj_cpf = company.cnpj_cpf

    def _inverse_state(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.write(
                {"state_id": company.state_id.id, "inscr_est": company.inscr_est}
            )

    def _inverse_state_tax_number_ids(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            state_tax_number_ids = self.env["state.tax.numbers"]
            for ies in company.state_tax_number_ids:
                state_tax_number_ids |= ies
            company.partner_id.state_tax_number_ids = state_tax_number_ids

    def _inverse_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_mun = company.inscr_mun

    def _inverse_city_id(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.city_id = company.city_id

    def _inverse_suframa(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.suframa = company.suframa

    legal_name = fields.Char(
        string="Legal Name",
        compute="_compute_l10n_br_data",
        inverse="_inverse_legal_name",
        size=128,
    )

    district = fields.Char(
        string="District",
        compute="_compute_l10n_br_data",
        inverse="_inverse_district",
        size=32,
    )

    city_id = fields.Many2one(
        string="City of Address",
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
        compute="_compute_l10n_br_data",
        inverse="_inverse_city_id",
    )

    country_id = fields.Many2one(default=lambda self: self.env.ref("base.br"))

    cnpj_cpf = fields.Char(
        string="CNPJ",
        compute="_compute_l10n_br_data",
        inverse="_inverse_cnpj_cpf",
        size=18,
    )

    inscr_est = fields.Char(
        string="State Tax Number",
        compute="_compute_l10n_br_data",
        inverse="_inverse_state",
        size=16,
    )

    state_tax_number_ids = fields.One2many(
        string="State Tax Numbers",
        comodel_name="state.tax.numbers",
        inverse_name="partner_id",
        compute="_compute_l10n_br_data",
        inverse="_inverse_state_tax_number_ids",
        ondelete="cascade",
    )

    inscr_mun = fields.Char(
        string="Municipal Tax Number",
        compute="_compute_l10n_br_data",
        inverse="_inverse_inscr_mun",
        size=18,
    )

    suframa = fields.Char(
        string="Suframa",
        compute="_compute_l10n_br_data",
        inverse="_inverse_suframa",
        size=18,
    )

    @api.model
    def _fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(Company, self)._fields_view_get(
            view_id, view_type, toolbar, submenu
        )
        if view_type == "form":
            res["arch"] = self._fields_view_get_address(res["arch"])
        return res

    @api.onchange("state_id")
    def _onchange_state(self):
        self.city_id = None

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):
        if self.cnpj_cpf:
            self.cnpj_cpf = cnpj_cpf.formata(self.cnpj_cpf)

    @api.onchange("city_id")
    def _onchange_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int city_id: id do city_id digitado.

        return: dicionário com o nome e id do município.
        """
        self.city = self.city_id.name

    @api.onchange("zip")
    def _onchange_zip(self):
        if self.zip:
            self.zip = misc.format_zipcode(self.zip, self.country_id.code)

    @api.multi
    def write(self, values):
        try:
            result = super(Company, self).write(values)
        except Exception:
            if not config["without_demo"] and values.get("currency_id"):
                result = models.Model.write(self, values)
            else:
                raise Exception

        return result
