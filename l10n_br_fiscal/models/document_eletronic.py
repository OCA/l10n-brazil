# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class EletronicDocument(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.eletronic'
    _description = 'Fiscal Document'

    def consultar(self):
        pass

    def transmitir(self):
        pass

    def cancelar(self):
        pass
