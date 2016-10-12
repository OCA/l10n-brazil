# -*- coding: utf-8 -*-
#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <michellstut@gmail.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.multi
    def zip_search(self):
        self.ensure_one()
        return self.env['l10n_br.zip'].zip_search(self)
