# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import models, fields
from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    item_original_id = fields.Many2one(
        comodel_name='sped.documento.item.original',
        string='Item original da NF',
        index=True,
        ondelete='cascade',
    )
