# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo import api, fields, models


class SpedDocumentoDuplicata(SpedBase, models.Model):
    _inherit = b'sped.documento.duplicata'

    id_fila_status = fields.Char(
        string=u'Status IdFila Sefaz'
    )
