# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("focusnfe", "FocusNFe"),
        ]
    )
    
    token_focus_homologacao = fields.Char(
        string="FocusNFe Homologação Token",
    )
    
    token_focus_producao = fields.Char(
        string="FocusNFe Produção Token",
    )