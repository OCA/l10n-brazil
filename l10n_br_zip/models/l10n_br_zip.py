# Copyright (C) 2012  Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")

_logger = logging.getLogger(__name__)

try:
    from pycep_correios import get_address_from_cep, WebService
except ImportError:
    _logger.warning("Library PyCEP-Correios not installed !")


class L10nBrZip(models.Model):
    """ Este objeto persiste todos os códigos postais que podem ser
    utilizados para pesquisar e auxiliar o preenchimento dos endereços.
    """

    _name = "l10n_br.zip"
    _description = "CEP"
    _rec_name = "zip_code"

    zip_code = fields.Char(string="CEP", size=8, required=True)

    street_type = fields.Char(string="Street Type", size=26)

    zip_complement = fields.Char(string="Range", size=200)

    street = fields.Char(string="Logradouro", size=72)

    district = fields.Char(string="District", size=72)

    country_id = fields.Many2one(comodel_name="res.country", string="Country")

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id','=',country_id)]",
    )

    city_id = fields.Many2one(
        comodel_name="res.city",
        string="City",
        required=True,
        domain="[('state_id','=',state_id)]",
    )

    def _set_domain(
        self,
        country_id=False,
        state_id=False,
        city_id=False,
        district=False,
        street=False,
        zip_code=False,
    ):
        domain = []
        if zip_code:
            new_zip = misc.punctuation_rm(zip_code or "")
            domain.append(("zip_code", "=", new_zip))
        else:
            if not state_id or not city_id or len(street or "") == 0:
                raise UserError(_("Necessário informar Estado, município e logradouro"))

            if country_id:
                domain.append(("country_id", "=", country_id))
            if state_id:
                domain.append(("state_id", "=", state_id))
            if city_id:
                domain.append(("city_id", "=", city_id))
            if district:
                domain.append(("district", "ilike", district))
            if street:
                domain.append(("street", "ilike", street))

        return domain

    @api.multi
    def _zip_update(self):
        self.ensure_one()
        cep_update_days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_zip.cep_update_days", default=365)
        )
        date_delta = fields.Datetime.today() - self.write_date
        if date_delta.days >= cep_update_days:
            cep_values = self._consultar_cep(self.zip_code)
            if cep_values:
                # Update zip object
                self.write(cep_values)

    @api.multi
    def set_result(self):
        self.ensure_one()
        self._zip_update()
        return {
            "country_id": self.country_id.id,
            "state_id": self.state_id.id,
            "city_id": self.city_id.id,
            "city": self.city_id.name,
            "district": self.district,
            "street": ((self.street_type or "") + " " + (self.street or ""))
            if self.street_type
            else (self.street or ""),
            "zip": misc.format_zipcode(self.zip_code, self.country_id.code),
        }

    def _consultar_cep(self, zip_code):
        zip_str = misc.punctuation_rm(zip_code)
        try:
            cep_ws_providers = {
                'apicep': WebService.APICEP,
                'viacep': WebService.VIACEP,
                'correios': WebService.CORREIOS,
            }
            cep_ws_provide = str(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_zip.cep_ws_provider", default="correios")
            )
            cep = get_address_from_cep(
                zip_str, webservice=cep_ws_providers.get(cep_ws_provide))
        except Exception as e:
            raise UserError(_("Erro no PyCEP-Correios : ") + str(e))

        values = {}
        if cep and any(cep.values()):
            # Search Brazil id
            country = self.env["res.country"].search(
                [("code", "=", "BR")], limit=1)

            # Search state with state_code and country id
            state = self.env["res.country.state"].search([
                ("code", "=", cep.get("uf")),
                ("country_id", "=", country.id)], limit=1)

            # search city with name and state
            city = self.env["res.city"].search([
                ("name", "=", cep.get("cidade")),
                ("state_id.id", "=", state.id)], limit=1)

            values = {
                "zip_code": zip_str,
                "street": cep.get("logradouro"),
                "zip_complement": cep.get("complemento"),
                "district": cep.get("bairro"),
                "city_id": city.id or False,
                "state_id": state.id or False,
                "country_id": country.id or False,
            }
        return values

    @api.model
    def zip_search(self, obj):

        try:
            domain = self._set_domain(
                country_id=obj.country_id.id,
                state_id=obj.state_id.id,
                city_id=obj.city_id.id,
                district=obj.district,
                street=obj.street,
                zip_code=obj.zip,
            )
        except AttributeError as e:
            raise UserError(_("Erro a Carregar Atributo: ") + str(e))

        zips = self.search(domain)

        # One ZIP was found
        if len(zips) == 1:
            obj.write(zips[0].set_result())
            return True

        # More than one ZIP was found
        elif len(zips) > 1:

            return self.create_wizard(obj, zips)

        # Address not found in local DB, search by PyCEP-Correios
        elif not zips and obj.zip:

            cep_values = self._consultar_cep(obj.zip)

            if cep_values:
                # Create zip object
                z = self.create(cep_values)
                obj.write(z.set_result())
                return True

    def create_wizard(self, obj, zips):

        context = dict(self.env.context)
        context.update({"address_id": obj.id, "object_name": obj._name})

        wizard = self.env["l10n_br.zip.search"].create(
            {
                "zip": obj.zip,
                "street": obj.street,
                "district": obj.district,
                "country_id": obj.country_id.id,
                "state_id": obj.state_id.id,
                "city_id": obj.city_id.id,
                "zip_ids": [[6, 0, [zip.id for zip in zips]]],
                "address_id": obj.id,
                "object_name": obj._name,
            }
        )

        return {
            "name": "Zip Search",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "l10n_br.zip.search",
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
            "nodestroy": True,
            "res_id": wizard.id,
            "context": context,
        }

    @api.multi
    def zip_select(self):
        self.ensure_one()
        address_id = self._context.get("address_id")
        object_name = self._context.get("object_name")
        if address_id and object_name:
            obj = self.env[object_name].browse(address_id)
            obj.write(self.set_result())
        return True
