# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo import api, fields, models, _
from mdfelib.v3_00.mdfe import (
    lacresType,
)
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


class L10n_brMdfeLacre(models.Model):
    _inherit = b'l10n_br.mdfe.lacre'

    def monta_mdfe(self):
        lacres = []

        for record in self:
            lacres.append(
                lacresType(nLacre=record.name)
            )
        return lacres
