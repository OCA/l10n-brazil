# Copyright (C) 2012 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
    from erpbrasil.base.fiscal import cnpj_cpf, ie
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class Lead(models.Model):
    """CRM Lead Case"""

    _inherit = "crm.lead"

    legal_name = fields.Char(
        string="Legal Name", size=128, help="nome utilizado em documentos fiscais"
    )

    cnpj = fields.Char(string="CNPJ", size=18)

    inscr_est = fields.Char(string="Inscr. Estadual/RG", size=16)

    inscr_mun = fields.Char(string="Inscr. Municipal", size=18)

    suframa = fields.Char(string="Suframa", size=18)

    city_id = fields.Many2one(
        comodel_name="res.city",
        string="City ID",
        domain="[('state_id', '=', state_id)]",
    )

    country_id = fields.Many2one(default=lambda self: self.env.ref("base.br"))

    district = fields.Char(string="District", size=32)

    street_number = fields.Char(string="Número", size=10)

    name_surname = fields.Char(
        string="Nome e sobrenome", size=128, help="Nome utilizado em documentos fiscais"
    )

    cpf = fields.Char(string="CPF", size=18)

    rg = fields.Char(string="RG", size=16)

    @api.multi
    @api.constrains("cnpj")
    def _check_cnpj(self):
        for record in self:
            country_code = record.country_id.code or ""
            if record.cnpj and country_code.upper() == "BR":
                cnpj = misc.punctuation_rm(record.cnpj)
                if not cnpj_cpf.validar(cnpj):
                    raise ValidationError(_("CNPJ: {} Invalid!").format(cnpj))

    @api.multi
    @api.constrains("cpf")
    def _check_cpf(self):
        for record in self:
            country_code = record.country_id.code or ""
            if record.cpf and country_code.upper() == "BR":
                cpf = misc.punctuation_rm(record.cpf)
                if not cnpj_cpf.validar(cpf):
                    raise ValidationError(_("CPF: {} Invalid!").format(cpf))

    @api.multi
    @api.constrains("inscr_est")
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise
        """
        for record in self:
            if record.inscr_est and record.cnpj and record.state_id:
                state_code = record.state_id.code or ""
                if not ie.validar(state_code.lower(), record.inscr_est):
                    raise ValidationError(
                        _("Inscrição Estadual: {} Invalida!".format(record.inscr_est))
                    )

    @api.onchange("cnpj", "country_id")
    def _onchange_cnpj(self):
        self.cnpj = cnpj_cpf.formata(self.cnpj)

    @api.onchange("cpf", "country_id")
    def _onchange_mask_cpf(self):
        self.cpf = cnpj_cpf.formata(self.cpf)

    @api.onchange("city_id")
    def _onchange_city_id(self):
        """Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        param int l10n_br_city_id: id do l10n_br_city_id digitado.
        return: dicionário com o nome e id do município.
        """
        if self.city_id:
            self.city = self.city_id.name

    @api.onchange("zip")
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip, self.country_id.code)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        result = super(Lead, self)._onchange_partner_id_values(
            self.partner_id.id if self.partner_id else False
        )

        if self.partner_id:
            result["street_number"] = self.partner_id.street_number
            result["district"] = self.partner_id.district
            result["city_id"] = self.partner_id.city_id.id
            if self.partner_id.is_company:
                result["legal_name"] = self.partner_id.legal_name
                result["cnpj"] = self.partner_id.cnpj_cpf
                result["inscr_est"] = self.partner_id.inscr_est
                result["suframa"] = self.partner_id.suframa
            else:
                result["cpf"] = self.partner_id.cnpj_cpf
                result["name_surname"] = self.partner_id.legal_name
        self.update(result)

    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        """extract data from lead to create a partner
        :param name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)
        :returns res.partner record
        """
        values = super(Lead, self)._create_lead_partner_data(
            name, is_company, parent_id
        )
        values.update(
            {
                "street_number": self.street_number,
                "district": self.district,
                "city_id": self.city_id.id,
            }
        )
        if is_company:
            values.update(
                {
                    "legal_name": self.legal_name,
                    "cnpj_cpf": self.cnpj,
                    "inscr_est": self.inscr_est,
                    "inscr_mun": self.inscr_mun,
                    "suframa": self.suframa,
                }
            )
        else:
            values.update(
                {
                    "legal_name": self.name_surname,
                    "cnpj_cpf": self.cpf,
                    "inscr_est": self.rg,
                }
            )
        return values
