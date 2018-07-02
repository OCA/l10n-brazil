# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedTransmissao(models.Model):

    _inherit = 'sped.transmissao'

    @api.multi
    def r1000(self):
        self.ensure_one()

        # Cria o registro
        R1000 = pysped.efdreinf.leiaute.R1000_1()

        # Popula ideEvento
        R1000.evento.ideEvento.tpAmb.valor = self.ambiente
        R1000.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        R1000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0
        if self.limpar_db:
            R1000.evento.ideEvento.verProc.valor = 'RemoverContribuinte'

        # Popula ideContri (Dados do Contribuinte)
        R1000.evento.ideContri.tpInsc.valor = '1'
        R1000.evento.ideContri.nrInsc.valor = limpa_formatacao(self.origem.cnpj_cpf)[0:8]

        # Popula infoContri
        R1000.evento.infoContri.operacao = 'I'
        R1000.evento.infoContri.idePeriodo.iniValid.valor = self.origem.periodo_id.code[
                                                            3:7] + '-' + self.origem.periodo_id.code[0:2]

        # Popula infoContri.InfoCadastro
        R1000.evento.infoContri.infoCadastro.classTrib.valor = self.origem.classificacao_tributaria_id.codigo
        if self.limpar_db:
            R1000.evento.infoContri.infoCadastro.classTrib.valor = '00'

        R1000.evento.infoContri.infoCadastro.indEscrituracao.valor = self.origem.ind_escrituracao
        R1000.evento.infoContri.infoCadastro.indDesoneracao.valor = self.origem.ind_desoneracao
        R1000.evento.infoContri.infoCadastro.indAcordoIsenMulta.valor = self.origem.ind_acordoisenmulta
        R1000.evento.infoContri.infoCadastro.indSitPJ.valor = self.origem.ind_sitpj
        R1000.evento.infoContri.infoCadastro.contato.nmCtt.valor = self.origem.nmctt
        R1000.evento.infoContri.infoCadastro.contato.cpfCtt.valor = self.origem.cpfctt
        R1000.evento.infoContri.infoCadastro.contato.foneFixo.valor = self.origem.cttfonefixo
        if self.origem.cttfonecel:
            R1000.evento.infoContri.infoCadastro.contato.foneCel.valor = self.origem.cttfonecel
        if self.origem.cttemail:
            R1000.evento.infoContri.infoCadastro.contato.email.valor = self.origem.cttemail

        # Gera ID do Evento
        data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
        R1000.gera_id_evento(dh_transmissao)

        # Grava o ID gerado
        self.id_evento = R1000.evento.Id.valor

        # Grava o XML gerado
        if self.envio_xml_id:
            envio = self.envio_xml_id
            envio.envio_xml_id = False
            envio.unlink()
        envio_xml = R1000.evento.xml
        envio_xml_nome = self.id_evento + '-envio.xml'
        anexo_id = self._grava_anexo(envio_xml_nome, envio_xml)
        self.envio_xml_id = anexo_id

        return R1000
