# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Danimar Ribeiro 22/08/2013                              #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
# Copyright (C) 2014  Luis Felipe Mileo - KMEE - www.kmee.com.br              #
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


import os
import re
import string
from PIL import Image
from StringIO import StringIO
from pyPdf import PdfFileReader, PdfFileWriter
from .certificado import Certificado
from .processor import ProcessadorNFe

from odoo.addons.nfe.tools.misc import mount_path_nfe

import logging
_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import ProcEventoCCe_100
    from pysped.nfe.danfe.danfe_geraldo import DANFE
    from pysped.nfe.danfe.daede import DAEDE
except ImportError as exc:
    logging.exception(exc.message)


def __processo(company):

    p = ProcessadorNFe(company)
    p.ambiente = int(company.nfe_environment)
    #p.versao = company.nfe_version
    p.estado = company.partner_id.l10n_br_city_id.state_id.code
    p.certificado = Certificado(company)
    p.salvar_arquivos = True
    p.contingencia_SCAN = False
    p.caminho = mount_path_nfe(company)
    return p


def monta_caminho_nfe(company, chave_nfe):
    p = __processo(company)
    return p.monta_caminho_nfe(p.ambiente, chave_nfe)


def monta_caminho_inutilizacao(
        company, data, serie, numero_inicial, numero_final):
    p = __processo(company)
    return p.monta_caminho_inutilizacao(
        p.ambiente, data, serie, numero_inicial, numero_final)


def check_key_nfe(company, chave_nfe, nfe=False):

    p = __processo(company)
    return p.consultar_nota(p.ambiente, chave_nfe, nfe)


def check_partner(company, cnpj_cpf, estado=None, ie=None):

    p = __processo(company)
    if not estado:
        estado = company.partner_id.state_id.code
    p.estado = estado
    cnpj_cpf = (
        re.sub(
            '[%s]' %
            re.escape(
                string.punctuation),
            '',
            cnpj_cpf or ''))
    return p.consultar_cadastro(estado, ie, cnpj_cpf)


def sign():
    pass


def send(company, nfe):

    p = __processo(company)
    # Busca a versão da NF a ser emitida, não a do cadastro da empresa
    p.versao = str(nfe[0].infNFe.versao.valor)
    p.danfe.logo = add_backgound_to_logo_image(company)
    p.danfe.leiaute_logo_vertical = company.nfe_logo_vertical
    p.danfe.salvar_arquivo = company.danfe_automatic_generate
    p.danfe.nome_sistema = company.nfe_email or \
        u"""Odoo/OpenERP - Sistema de Gestao Empresarial de Codigo Aberto
        - 100%% WEB - www.openerpbrasil.org"""

    return p.processar_notas(nfe)


def cancel(company, nfe_access_key, nfe_protocol_number, justificative):

    p = __processo(company)
    return p.cancelar_nota_evento(
        chave_nfe=nfe_access_key,
        numero_protocolo=nfe_protocol_number,
        justificativa=justificative
    )


def invalidate(company, invalidate_number):

    p = __processo(company)
    cnpj_partner = re.sub('[^0-9]', '', company.partner_id.cnpj_cpf)
    serie = invalidate_number.document_serie_id.code
    return p.inutilizar_nota(
        cnpj=cnpj_partner,
        serie=serie,
        numero_inicial=invalidate_number.number_start,
        numero_final=invalidate_number.number_end,
        justificativa=invalidate_number.justificative)


def send_correction_letter(company, chave_nfe, numero_sequencia, correcao):

    p = __processo(company)
    return p.corrigir_nota_evento(
        p.ambiente, chave_nfe, numero_sequencia, correcao)


def print_danfe(invoices):
    str_pdf = ""
    paths = []

    for inv in invoices:
        if inv.nfe_version == '1.10':
            from pysped.nfe.leiaute import ProcNFe_110
            procnfe = ProcNFe_110()
        elif inv.nfe_version == '2.00':
            from pysped.nfe.leiaute import ProcNFe_200
            procnfe = ProcNFe_200()
        elif inv.nfe_version == '3.10':
            from pysped.nfe.leiaute import ProcNFe_310
            procnfe = ProcNFe_310()
        elif inv.nfe_version == '4.00':
            from pysped.nfe.leiaute import ProcNFe_400
            procnfe = ProcNFe_400()

        file_xml = monta_caminho_nfe(inv.company_id, inv.nfe_access_key)
        if inv.state not in ('open', 'paid', 'sefaz_cancelled'):
            file_xml = os.path.join(file_xml, 'tmp/')
        procnfe.xml = os.path.join(file_xml, inv.nfe_access_key + '-nfe.xml')
        danfe = DANFE()
        danfe.logo = add_backgound_to_logo_image(inv.company_id)
        danfe.NFe = procnfe.NFe
        danfe.leiaute_logo_vertical = inv.company_id.nfe_logo_vertical
        danfe.protNFe = procnfe.protNFe
        danfe.caminho = "/tmp/"
        danfe.gerar_danfe()
        paths.append(danfe.caminho + danfe.NFe.chave + '.pdf')
        inv.is_danfe_printed = True

        if inv.cce_document_event_ids:
            daede = DAEDE()
            daede.logo = add_backgound_to_logo_image(inv.company_id)
            daede.NFe = procnfe.NFe
            daede.protNFe = procnfe.protNFe
            for item, event in enumerate(inv.cce_document_event_ids):
                proc_evento = ProcEventoCCe_100()
                doc_item = str(item + 1).zfill(2)
                proc_evento.xml = os.path.join(
                    file_xml,
                    inv.nfe_access_key + '-' +
                    doc_item + '-cce.xml')
                daede.procEventos.append(proc_evento)

            daede.caminho = "/tmp/"
            daede.gerar_daede()
            paths.append(daede.caminho + 'eventos-' + daede.NFe.chave + '.pdf')

    output = PdfFileWriter()
    s = StringIO()

    # merge dos pdf criados
    for path in paths:
        pdf = PdfFileReader(file(path, "rb"))

        for i in range(pdf.getNumPages()):
            output.addPage(pdf.getPage(i))

        output.write(s)

    str_pdf = s.getvalue()
    s.close()

    return str_pdf


def add_backgound_to_logo_image(company):
    logo = company.nfe_logo or company.logo
    logo_image = Image.open(StringIO(logo.decode('base64')))
    image_path = os.path.join(mount_path_nfe(company), 'company_logo.png')

    bg = Image.new("RGB", logo_image.size, (255, 255, 255))
    bg.paste(logo_image, logo_image)
    bg.save(image_path)

    return image_path
