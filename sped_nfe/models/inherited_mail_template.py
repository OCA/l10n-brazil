# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def generate_email(self, res_ids, fields=None):
        self.ensure_one()

        multi_mode = True
        if isinstance(res_ids, (int, long)):
            res_ids = [res_ids]
            multi_mode = False

        res = super(MailTemplate, self).generate_email(res_ids, fields=fields)

        if self.model not in \
            ('sped.documento', 'sped.documento.carta.correcao'):
            return multi_mode and res or res[res_ids[0]]

        for res_id in res:
            busca = [
                ('res_model', '=', self.model),
                ('res_id', '=', res_id),
            ]

            attachments = self.env['ir.attachment'].search(busca)

            if len(attachments) > 0:
                if not 'attachment_ids' in res[res_id]:
                    res[res_id]['attachment_ids'] = []

                for attachment in attachments:
                    res[res_id]['attachment_ids'].append(attachment.id)

        return multi_mode and res or res[res_ids[0]]
