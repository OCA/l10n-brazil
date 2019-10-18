# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class L10nBrZipSearch(models.TransientModel):
    _name = "l10n_br.zip.search"
    _description = "Zipcode Search"

    zip = fields.Char(string="CEP", size=8)

    street = fields.Char(string="Logradouro", size=72)

    district = fields.Char(string="District", size=72)

    country_id = fields.Many2one(string="Country", comodel_name="res.country")

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id', '=', country_id)]",
    )

    city_id = fields.Many2one(
        comodel_name="res.city", string="Cidade", domain="[('state_id', '=', state_id)]"
    )

    zip_ids = fields.Many2many(
        comodel_name="l10n_br.zip",
        relation="zip_search",
        column1="zip_search_id",
        column2="zip_id",
        string="CEPs",
        readonly=False,
    )

    state = fields.Selection(
        selection=[("init", "init"), ("done", "done")],
        string="state",
        readonly=True,
        default="init",
    )

    address_id = fields.Integer(string="Id do objeto", invisible=True)

    object_name = fields.Char(string="Nome do Objeto", size=100, invisible=True)

    @api.model
    def default_get(self, fields_list):
        data = super(L10nBrZipSearch, self).default_get(fields_list)

        context = dict(self._context or {})
        data["zip"] = context.get("zip", False)
        data["street"] = context.get("street", False)
        data["district"] = context.get("district", False)
        data["country_id"] = context.get("country_id", False)
        data["state_id"] = context.get("state_id", False)
        data["city_id"] = context.get("city_id", False)
        data["address_id"] = context.get("address_id", False)
        data["object_name"] = context.get("object_name", False)

        data["zip_ids"] = context.get("zip_ids", False)
        data["state"] = "done"

        return data

    @api.multi
    def zip_search(self):

        self.ensure_one()
        data = self
        obj_zip = self.env["l10n_br.zip"]

        domain = obj_zip._set_domain(
            country_id=data.country_id.id,
            state_id=data.state_id.id,
            city_id=data.city_id.id,
            district=data.district,
            street=data.street,
            zip_code=data.zip,
        )

        # Search zips
        zip_ids = obj_zip.search(domain)

        context = dict(self.env.context)
        context.update({"address_id": data.address_id, "object_name": data.object_name})

        self.write({"state": "done", "zip_ids": [[6, 0, [zip.id for zip in zip_ids]]]})

        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_br.zip.search",
            "view_mode": "form",
            "view_type": "form",
            "res_id": data.id,
            "views": [(False, "form")],
            "target": "new",
            "nodestroy": True,
            "context": context,
        }

    @api.multi
    def zip_new_search(self):
        data = self.read()[0]
        self.ensure_one()
        self.write({"state": "init", "zip_ids": [[6, 0, []]]})

        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_br.zip.search",
            "view_mode": "form",
            "view_type": "form",
            "res_id": data["id"],
            "views": [(False, "form")],
            "target": "new",
            "nodestroy": True,
        }
