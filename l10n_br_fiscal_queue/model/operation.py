# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class FiscalOperation(models.Model):
    _inherit = 'l10n_br_fiscal.operation'

    momento_envio_documento = fields.Selection(
        selection=[
            ('now', 'Enviar Imediatamente'),
            ('with_delay', 'Enviar Depois'),
        ],
        string='Momento de transmissão',
        default='now',
        required=True,
    )
