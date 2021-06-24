# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from lxml import etree

from odoo import api, fields, models
from odoo.osv import expression, orm


class DataAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.data.abstract"
    _description = "Fiscal Data Abstract"
    _order = "code"

    code = fields.Char(string="Code", required=True, index=True)

    name = fields.Text(string="Name", required=True, index=True)

    code_unmasked = fields.Char(
        string="Unmasked Code", compute="_compute_code_unmasked", store=True, index=True
    )

    @api.depends("code")
    def _compute_code_unmasked(self):
        for r in self:
            # TODO mask code and unmasck
            r.code_unmasked = misc.punctuation_rm(r.code)

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        model_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "search":
            doc = etree.XML(model_view["arch"])
            for node in doc.xpath("//field[@name='code']"):
                node.set(
                    "filter_domain",
                    "['|', '|', ('code', 'ilike', self), "
                    "('code_unmasked', 'ilike', self + '%'),"
                    "('name', 'ilike', self + '%')]",
                )

                orm.setup_modifiers(node)
            model_view["arch"] = etree.tostring(doc)

        return model_view

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if operator == "ilike" and not (name or "").strip():
            domain = []
        elif operator in ("ilike", "like", "=", "=like", "=ilike"):
            domain = expression.AND(
                [
                    args or [],
                    [
                        "|",
                        "|",
                        ("name", operator, name),
                        ("code", operator, name),
                        ("code_unmasked", "ilike", name + "%"),
                    ],
                ]
            )
            recs = self._search(
                expression.AND([domain, args]),
                limit=limit,
                access_rights_uid=name_get_uid,
            )
            return self.browse(recs).name_get()

        return super()._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )

    def name_get(self):
        def truncate_name(name):
            if len(name) > 60:
                name = "{}...".format(name[:60])
            return name

        if self._context.get("show_code_only"):
            return [(r.id, "{}".format(r.code)) for r in self]

        return [(r.id, "{} - {}".format(r.code, truncate_name(r.name))) for r in self]
