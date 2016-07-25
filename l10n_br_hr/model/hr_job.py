# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm, fields
from openerp.tools.translate import _

class HrJob(orm.Model):
    
    _inherit = 'hr.job'

    _columns = {
            'cbo_id' : fields.many2one('l10n_br_hr.cbo', 'CBO'),
    }