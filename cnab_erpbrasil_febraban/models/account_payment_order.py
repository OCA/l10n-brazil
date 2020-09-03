# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, models, fields
from ..febraban.cnab import Cnab

_logger = logging.getLogger(__name__)

try:
    from erpbrasi.febraban.cnab.tipos import Arquivo, Lote

    from cnab240.errors import (Cnab240Error)
except ImportError as err:
    _logger.debug = err


class AccountPaymentOrder(models.Model):

    _inherit = 'account.payment.order'

    def _generate_payment_file(self):
        try:
            return Cnab.gerar_remessa(order=self), self.name + '.REM'
        except Cnab240Error as e:
            _logger.error("Erro ao gerar o arquivo: \n\n{0}".format(e))

    @api.multi
    def generate_payment_file(self):
        """Returns (payment file as string, filename)"""
        self.ensure_one()
        if self.payment_method_id.code in ('240', '400', '500'):
            return self._generate_payment_file()
        return super(AccountPaymentOrder, self).generate_payment_file()
