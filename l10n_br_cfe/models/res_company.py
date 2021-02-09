# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import logging
import os

from odoo import fields, models
from odoo.tools import config
from odoo.addons.l10n_br_cfe.constants.fiscal import (
    AMBIENTE_CFE,
    TIPO_EMISSAO_CFE,
    TIPO_CONEXAO_PROCESSADOR_CFE
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.misc import punctuation_rm
    from satcfe import BibliotecaSAT

except (ImportError, IOError) as err:
    _logger.debug(err)


class ResCompany(models.Model):
    _inherit = 'res.company'

    ambiente_cfe = fields.Selection(
        selection=AMBIENTE_CFE,
        string='Ambiente NFC-e'
    )
    tipo_emissao_cfe = fields.Selection(
        selection=TIPO_EMISSAO_CFE,
        string='Tipo de emissão CF-e'
    )
    tipo_emissao_cfe_contingencia = fields.Selection(
        selection=TIPO_EMISSAO_CFE,
        string='Tipo de emissão CF-e contingência'
    )
    logo_cfe = fields.Binary(
        string='Logo no CF-E',
        attachment=True,
    )
    tipo_processador_cfe = fields.Selection(
        string="Tipo instalação SAT",
        selection=TIPO_CONEXAO_PROCESSADOR_CFE,
    )

    @property
    def caminho_sped(self):
        """ Local no filestore em que os arquivos xml dos CF-e
        são salvos.
        """
        filestore = config.filestore(self._cr.dbname)
        return os.path.join(filestore, 'sped', punctuation_rm(self.cnpj_cpf))

    def processador_cfe(self):
        """
        Busca classe do processador do cadastro da empresa,
        onde podemos ter três tipos de processamento dependendo
        de onde o equipamento esta instalado:

        - Instalado no mesmo servidor que o Odoo;
        - Instalado na mesma rede local do servidor do Odoo;
        - Instalado em um local remoto onde o browser vai ser
        responsável por se comunicar com o equipamento

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
