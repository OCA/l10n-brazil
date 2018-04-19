# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from mdfelib.v3_00.mdfe import (
    segType,
    infSegType,
    infRespType,
)
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


class L10nBrMdfeSeguro(models.Model):
    _inherit = b'l10n_br.mdfe.seguro'

    def _prepara_resp_type(self):
        pass

    def _prepara_seg_type(self):
        # inf_seg_type = []
        # inf_seg_type.append(
        #     infSegType(
        #         xSeg=record.responsavel_seguro,
        #         CNPJ=punctuation_rm(record.responsavel_cnpj_cpf),
        #     )
        # )
        pass

    def monta_mdfe(self):
        seg = []
        return seg
