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
    def _get_recurrent_fields(self):
        res = super(L10nBrHrCalendar, self)._get_recurrent_fields()
        res.append('models_id')
        return res

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

    @api.model
    def get_date_formats(self):
        lang = self._context.get("lang") or self.env.user.lang or ''
        res_lang_obj = self.env['res.lang']
        lang_params = {}

        lang_id = res_lang_obj.search([("code", "=", lang)])
        if lang_id:
            lang_params = {
                'date_format': lang_id.date_format,
                'time_format': lang_id.time_format,
            }

        # formats will be used for str{f,p}time() which do
        # not support unicode in Python 2, coerce to str
        format_date = \
            lang_params.get("date_format", '%B-%d-%Y').encode('utf-8')
        format_time = \
            lang_params.get("time_format", '%I-%M %p').encode('utf-8')
        return (format_date, format_time)

    @api.multi
    def unlink(self):
        """
        Validação que permite apenas ao grupo de Gerente de RH à excluir
        eventos do calendario, que tenham um holidays atrelado
        """
        if not self.env.user.has_group('base.group_hr_manager'):
            if self.models_id.id == \
                    self.env.ref('hr_holidays.model_hr_holidays').id:
                raise Warning(
                    'Ocorrências já aprovadas somente podem ser rejeitadas '
                    'por usuários com perfil de Gerente de RH')
        return super(L10nBrHrCalendar, self).unlink()
