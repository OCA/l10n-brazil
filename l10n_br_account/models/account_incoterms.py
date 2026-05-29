# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountIncoterms(models.Model):
    _inherit = "account.incoterms"

    def _compute_display_name(self):
        # No Brasil muitas pessoas conhecem os tipos de frete mais pelo
        # Codigo do que pela descrição, por isso aqui está sendo feito
        # "Codigo - Descrição" ex.:
        # CIF - Custo, Seguro e Frete; FOB - Gratis a Bordo, etc
        for record in self:
            name = record.name
            # Caso o name seja muito grande ao mostrar o campo na
            # visão acaba ficando fora da tela o que dificulta a
            # visualização, ao clicar em Pesquisar é mostrado o
            # name completo
            if len(record.name) > 150:
                name = record.name[:150] + " ..."
            record.display_name = f"{record.code} - {name}"
