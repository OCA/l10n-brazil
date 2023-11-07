# Copyright 2023 - TODAY, KMEE INFORMATICA LTDA
# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("focusnfe", "FocusNFe"),
        ]
    )

    focusnfe_production_token = fields.Char(
        string="FocusNFe Production Token",
    )

    focusnfe_homologation_token = fields.Char(
        string="FocusNFe Homologation Token",
    )

    focusnfe_nfse_service_type_value = fields.Selection(
        [
            ("item_lista_servico", "Service Type"),
            ("codigo_tributacao_municipio", "City Taxation Code"),
        ],
        string="NFSE Service Type Value",
        default="item_lista_servico",
    )

    focusnfe_nfse_cnae_code_value = fields.Selection(
        [
            ("codigo_cnae", "CNAE Code"),
            ("codigo_tributacao_municipio", "City Taxation Code"),
        ],
        string="NFSE CNAE Code Value",
        default="codigo_cnae",
    )

    def get_focusnfe_token(self):
        """
        Retrieves the appropriate FocusNFe API token for the current NFSe environment setting.
        This method decides between the production and homologation (test) tokens based on the
        'nfse_environment' field of the record.

        Preconditions:
        - The method must be called on a single record (ensure_one is used to enforce this).

        Returns:
        - str: The FocusNFe token. It returns the production token if 'nfse_environment'
        is set to "1", otherwise, it returns the homologation token.

        Raises:
        - ValueError: If called on a recordset containing more than one record.
        """
        self.ensure_one()
        return (
            self.focusnfe_production_token
            if self.nfse_environment == "1"
            else self.focusnfe_homologation_token
        )
