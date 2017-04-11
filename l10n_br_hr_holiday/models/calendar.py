# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, api
from openerp.osv.orm import setup_modifiers
from openerp.exceptions import Warning
from lxml import etree


class L10nBrHrCalendar(models.Model):
    _inherit = "calendar.event"

    models_id = fields.Many2one(
        comodel_name="ir.model",
        string="Modelo de Origem",
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(L10nBrHrCalendar, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu
        )
        if view_type == "form" and not res['name'] == u'Meetings Popup':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field")
            id_found = self.env.ref('hr_holidays.model_hr_holidays').id
            # or try to search for the id using the external id
            for node in nodes:
                node.set('attrs',
                         "{'readonly':[('models_id','=',%s)]}" % id_found)
                setup_modifiers(node, res['fields'])
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def unlink(self):
        if self.models_id.id == \
                self.env.ref("hr_holidays.model_hr_holidays").id:
            raise Warning('Evento de Recursos Humanos')
        return super(L10nBrHrCalendar, self).unlink()
