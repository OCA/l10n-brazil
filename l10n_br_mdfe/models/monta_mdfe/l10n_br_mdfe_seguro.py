# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    RESPONSAVEL_SEGURO,
)


class L10nBrMdfeSeguro(models.Model):
    _inherit = b'l10n_br.mdfe.seguro'

    def monta_mdfe(self):
        self.ensure_one()
        return
