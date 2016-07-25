# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm, fields
from openerp.tools.translate import _

class L10nBrHrCbo(orm.Model):

	_name = "l10n_br_hr.cbo"
	_description = "Brazilian Classification of Occupation"
	_columns = {
		'code': fields.integer('Code', required=True),
		'name': fields.char('Name', size=255, required=True, translate=True),
	}
