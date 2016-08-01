# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class L10nBrHrCbo(models.Model):
    _name = "l10n_br_hr.cbo"
    _description = "Brazilian Classification of Occupation"

    code = fields.Integer('Code', required=True)
    name = fields.Char('Name', size=255, required=True, translate=True)
