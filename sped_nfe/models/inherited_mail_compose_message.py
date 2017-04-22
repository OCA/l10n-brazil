# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import os
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    TIPO_EMISSAO_PROPRIA,
    SITUACAO_NFE_AUTORIZADA,
    SITUACAO_NFE_CANCELADA,
    SITUACAO_NFE_DENEGADA,
)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields):
        """ Handle composition mode. Some details about context keys:
            - comment: default mode, model and ID of a record the user comments
                - default_model or active_model
                - default_res_id or active_id
            - reply: active_id of a message the user replies to
                - default_parent_id or message_id or active_id: ID of the
                    mail.message we reply to
                - message.res_model or default_model
                - message.res_id or default_res_id
            - mass_mail: model and IDs of records the user mass-mails
                - active_ids: record IDs
                - default_model or active_model
        """
        res = super(MailComposeMessage, self).default_get(fields)

        model = res.get('model', self._context.get('active_model'))

        if model not in ('sped.documento', 'sped.documento.carta.correcao'):
            return res

        if res['composition_mode'] != 'comment':
            return res

        res_id = self._context.get('default_res_id')

        if not res_id:
            return res

        if model == 'sped.documento':
            documento = self.env['sped.documento'].browse(res_id)

        elif model == 'sped.documento.carta.correcao':
            carta_correcao = \
                self.env['sped.documento.carta.correcao'].browse(res_id)
            documento = carta_correcao.documento_id

        empresa = documento.empresa_id

        if documento.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return res

        if documento.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        mail_template = None
        if model == 'sped.documento':
            if documento.state_nfe == SITUACAO_NFE_AUTORIZADA:
                if documento.operacao_id.mail_template_id:
                    mail_template = documento.operacao_id.mail_template_id

                else:
                    if documento.modelo == MODELO_FISCAL_NFE and \
                            empresa.mail_template_nfe_autorizada_id:
                        mail_template = \
                            empresa.mail_template_nfe_autorizada_id

                    elif documento.modelo == MODELO_FISCAL_NFCE and \
                            empresa.mail_template_nfce_autorizada_id:
                        mail_template = \
                            empresa.mail_template_nfce_autorizada_id

            elif documento.state_nfe == SITUACAO_NFE_CANCELADA:
                if documento.modelo == MODELO_FISCAL_NFE and \
                        empresa.mail_template_nfe_cancelada_id:
                    mail_template = \
                        empresa.mail_template_nfe_cancelada_id

                elif documento.modelo == MODELO_FISCAL_NFCE and \
                        empresa.mail_template_nfce_cancelada_id:
                    mail_template = \
                        empresa.mail_template_nfce_cancelada_id

            elif documento.state_nfe == SITUACAO_NFE_DENEGADA:
                if documento.modelo == MODELO_FISCAL_NFE and \
                        empresa.mail_template_nfe_denegada_id:
                    mail_template = \
                        empresa.mail_template_nfe_denegada_id

                elif documento.modelo == MODELO_FISCAL_NFCE and \
                        empresa.mail_template_nfce_denegada_id:
                    mail_template = \
                        empresa.mail_template_nfce_denegada_id

        elif model == 'sped.documento.carta.correcao':
            if documento.modelo == MODELO_FISCAL_NFE:
                if empresa.mail_template_nfe_cce_id:
                    mail_template = empresa.mail_template_nfe_cce_id.id

            elif documento.modelo == MODELO_FISCAL_NFCE:
                if empresa.mail_template_nfce_cce_id:
                    mail_template = empresa.mail_template_nfce_cce_id.id

        if mail_template is None:
            return res

        res['template_id'] = mail_template.id

        valores = self.onchange_template_id(
            mail_template.id,
            res['composition_mode'],
            res['model'],
            res['res_id'],
        )['value']

        res.update(valores)

        return res
