# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
#   Luiz Felipe Divino <divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import models
from odoo.addons.sped_imposto.models.sped_calculo_imposto_item import \
    SpedCalculoImpostoItem
from odoo.addons.l10n_br_base.constante_tributaria import *


class InheritedSpedCalculoImpostoItem(SpedCalculoImpostoItem, models.Model):
    _inherit = b'sped.documento.item'

    def prepara_dados_documento_item(self):
        result = super(
            InheritedSpedCalculoImpostoItem, self
        ).prepara_dados_documento_item()

        if self.fci:
            result.update({'fci': self.fci})

        return result
