# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
import os

from odoo import fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    from pybrasil.inscricao import limpa_formatacao
    from satcfe import ClienteSATLocal
    from satcfe import ClienteSATHub
    from satcfe import BibliotecaSAT

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedEmpresa(models.Model):
    _inherit = 'sped.empresa'

    logo_cfe = fields.Binary(
        string='Logo no CF-E',
        attachment=True,
    )
    mail_template_cfe_autorizada_id = fields.Many2one(
        comodel_name='mail.template',
        string='Modelo de email para cfe autorizada',
        # domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_cfe_cancelada_id = fields.Many2one(
        comodel_name='mail.template',
        string='Modelo de email para cfe cancelada',
        # domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_cfe_denegada_id = fields.Many2one(
        comodel_name='mail.template',
        string='Modelo de email para cfe denegada',
        # domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    mail_template_cfe_cce_id = fields.Many2one(
        comodel_name='mail.template',
        string='Modelo de email para CC-e',
        # domain=[('model_id', '=', ref('sped.model_sped_documento'))],
    )
    tipo_processador_cfe = fields.Selection(
        string="Tipo instalação SAT",
        selection=[
            ('usb', 'Conectado na porta USB'),
            ('rede_local', 'Conectado em rede local/vpn'),
            ('nuvem', 'Conexão via navegador'),

        ]
    )

    @property
    def caminho_sped(self):
        filestore = config.filestore(self._cr.dbname)
        return os.path.join(filestore, 'sped', limpa_formatacao(self.cnpj_cpf))

    def processador_cfe(self):
        """
        Busca classe do processador do cadastro da empresa, onde podemos ter três tipos de processamento dependendo
        de onde o equipamento esta instalado:

        - Instalado no mesmo servidor que o Odoo;
        - Instalado na mesma rede local do servidor do Odoo;
        - Instalado em um local remoto onde o browser vai ser responsável por se comunicar com o equipamento

        :return:
        """
        self.ensure_one()
        # if ....
        #     return BibliotecaSAT, ClienteSATHub
        if self.tipo_processador_cfe == 'usb':
            from satcfe.clientelocal import ClienteSATLocal as Cliente
        elif self.tipo_processador_cfe == 'rede_local':
            from satcfe.clientesathub import ClienteSATHub as Cliente
        else:
            raise NotImplementedError
        return BibliotecaSAT, Cliente
