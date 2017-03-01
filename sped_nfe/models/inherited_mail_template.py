# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from ...mail.models.mail_template import (
    mako_safe_template_env,
    mako_template_env,
    format_date,
    format_tz,
)
import logging
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ...sped.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe import ProcessadorNFe
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora, formata_data, data_por_extenso)
    from pybrasil.valor import formata_valor, valor_por_extenso_unidade

except (ImportError, IOError) as err:
    _logger.debug(err)


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    auto_attachment = fields.Boolean(
        string=u'Automatic uses record''s attachments',
        default=True,
    )

    @api.model
    def render_template(self, template_txt, model, res_ids, post_process=False):
        """ Render the given template text, replace mako expressions ``${expr}``
        with the result of evaluating these expressions with an evaluation
        context containing:

         - ``user``: browse_record of the current user
         - ``object``: record of the document record this mail is related to
         - ``context``: the context passed to the mail composition wizard

        :param str template_txt: the template text to render
        :param str model: model name of the document record this mail is related to.
        :param int res_ids: list of ids of document records those mails are related to.
        """
        multi_mode = True
        if isinstance(res_ids, (int, long)):
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")

        # try to load the template
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        records = self.env[model].browse(filter(None, res_ids))  # filter to avoid browsing [None]
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {
            'formata_data': formata_data,
            'formata_valor': formata_valor,
            'valor_por_extenso': valor_por_extenso_unidade,
            'data_por_extenso': data_por_extenso,
            'parse_datetime': parse_datetime,
            'format_date': lambda date, format=False, context=self._context: format_date(self.env, date, format),
            'format_tz': lambda dt, tz=False, format=False, context=self._context: format_tz(self.env, dt, tz, format),
            'user': self.env.user,
            'usuario': self.env.user,
            'ctx': self._context,  # context kw would clash with mako internals
            'contexto': self._context,  # context kw would clash with mako internals
        }
        for res_id, record in res_to_rec.iteritems():
            variables['object'] = record
            variables['registro'] = record
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info("Failed to render template %r using values %r" % (template, variables), exc_info=True)
                raise UserError(_("Failed to render template %r using values %r")% (template, variables))
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.iteritems():
                results[res_id] = self.render_post_process(result)

        return multi_mode and results or results[res_ids[0]]

    @api.multi
    def generate_email(self, res_ids, fields=None):
        self.ensure_one()

        if not self.auto_attachment:
            return super(MailTemplate, self).generate_email(
                res_ids,
                fields=fields,
            )

        multi_mode = True

        if isinstance(res_ids, (int, long)):
            res_ids = [res_ids]
            multi_mode = False

        results = super(MailTemplate, self).generate_email(res_ids, fields=fields)

        attachment = self.env['ir.attachment']
        model = self.model
        for res_id in results:
            busca = [
                ('res_model', '=', model),
                ('res_id', '=', res_id),
            ]
            attachments = attachment.search(busca)

            if not attachments:
                continue

            if 'attachment_ids' not in results[res_id]:
                results[res_id]['attachment_ids'] = []

            for attachment in attachments:
                results[res_id]['attachment_ids'].append(attachment.id)

        return multi_mode and results or results[res_ids[0]]
