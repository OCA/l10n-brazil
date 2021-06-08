# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import re

from odoo import api, fields, models


class DFe(models.Model):
    _name = "l10n_br_fiscal.dfe"
    _description = "Consult DF-e"
    _order = "id desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    last_nsu = fields.Char(
        string="Last NSU",
        size=25,
        default="0",
    )
    last_query = fields.Datetime(
        string="Last query",
    )

    recipient_xml_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.dfe_xml",
        inverse_name="dfe_id",
        string="XML Documents",
    )

    @api.depends("company_id.name", "last_nsu")
    def name_get(self):
        return [
            (r.id, "{} - NSU: {}".format(r.company_id.name, r.last_nsu)) for r in self
        ]

    imported_document_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        inverse_name="dfe_id",
        string="Imported Documents",
    )

    imported_dfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.mdfe",
        inverse_name="dfe_id",
        string="Manifestações do Destinatário Importadas",
    )

    use_cron = fields.Boolean(
        default=False,
        string="Download new documents automatically",
        help="If activated, allows new manifestations to be automatically "
        "searched with a Cron",
    )

    def action_manage_manifestations(self):

        return {
            "name": self.company_id.legal_name,
            "view_mode": "tree,form",
            "res_model": "l10n_br_fiscal.mdfe",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": [("company_id", "=", self.company_id.id)],
            "limit": self.env["l10n_br_fiscal.mdfe"].search_count(
                [("company_id", "=", self.company_id.id)]
            ),
        }

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub("[^0-9]", "", cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (
                    val[0:2],
                    val[2:5],
                    val[5:8],
                    val[8:12],
                    val[12:14],
                )
        return cnpj


class DFeXML(models.Model):
    _name = "l10n_br_fiscal.dfe_xml"
    _description = "DF-e XML Document"

    dfe_id = fields.Many2one(
        string="DF-e Consult",
        comodel_name="l10n_br_fiscal.dfe",
    )

    xml_type = fields.Selection(
        [
            ("0", "Envio"),
            ("1", "Resposta"),
            ("2", "Resposta-LoteDistDFeInt"),
            ("3", "Resposta-LoteDistDFeInt-DocZip(NFe)"),
        ],
        string="XML Type",
    )

    xml = fields.Char(
        string="XML",
        size=5000,
    )
