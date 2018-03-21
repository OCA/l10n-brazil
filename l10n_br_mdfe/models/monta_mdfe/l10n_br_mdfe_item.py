# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL,
    SITUACAO_NFE,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_NFE,
)


class L10nBrMdfeItem(models.Model):
    _inherit = 'l10n_br.mdfe.item'

    def monta_mdfe(self):
        self.ensure_one()
        return
