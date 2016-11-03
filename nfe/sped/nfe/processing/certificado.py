# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015  Luis Felipe Mileo - KMEE - www.kmee.com.br              #
# Copyright (C) 2015  Rafael da Silva Lima - KMEE - www.kmee.com.br           #
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

import tempfile
import base64

import logging
_logger = logging.getLogger(__name__)

try:
    from pysped.xml_sped.certificado import Certificado as PySpedCertificado
except ImportError as exc:
    logging.exception(exc.message)


class Certificado(PySpedCertificado):

    def __init__(self, company):
        super(Certificado, self).__init__()
        self.certificado_file = self._caminho_certificado(company.nfe_a1_file)
        self.senha = company.nfe_a1_password

    def _caminho_certificado(self, nfe_a1_file):
        """

        :return: caminho do certificado
        """
        certificado_file = tempfile.NamedTemporaryFile()
        certificado_file.seek(0)
        certificado_file.write(
            base64.decodestring(nfe_a1_file))
        certificado_file.flush()
        self.arquivo = certificado_file.name
        return certificado_file
