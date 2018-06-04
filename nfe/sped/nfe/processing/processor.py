# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015  Luis Felipe Mileo - KMEE - www.kmee.com.br              #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from .certificado import Certificado

from openerp.addons.nfe.tools.misc import mount_path_nfe

import logging
_logger = logging.getLogger(__name__)

try:
    from pysped.nfe import ProcessadorNFe as ProcessadorNFePySped
    from pysped.nfe.danfe import DANFE as DanfePySped
    from pysped.nfe.danfe.daede import DAEDE
except ImportError as exc:
    logging.exception(exc.message)


class DANFE(DanfePySped):
    def __init__(self):
        super(DANFE, self).__init__()


class ProcessadorNFe(ProcessadorNFePySped):
    def __init__(self, company):
        super(ProcessadorNFe, self).__init__()
        self.ambiente = int(company.nfe_environment) or 2
        self.estado = company.partner_id.l10n_br_city_id.state_id.code
        self.versao = company.nfe_version
        self.certificado = Certificado(company)
        self.caminho = mount_path_nfe(company, 'nfe')
        self.salvar_arquivos = False
        self.contingencia_SCAN = False
        self.contingencia = False
        self.danfe = DANFE()
        self.daede = DAEDE()
        self.caminho_temporario = ''
        self.maximo_tentativas_consulta_recibo = 5
        self.consulta_servico_ao_enviar = False

        self._servidor = ''
        self._url = ''
        self._soap_envio = None
        self._soap_retorno = None
