# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedTransmissao(models.Model):
    _inherit = 'sped.transmissao'

    @api.multi
    def s1000(self):
        self.ensure_one()

        # Cria o registro
        S1000 = pysped.esocial.leiaute.S1000_2()

        # Popula ideEvento
        S1000.tpInsc = '1'
        S1000.nrInsc = limpa_formatacao(self.origem.cnpj_cpf)[0:8]
        S1000.evento.ideEvento.tpAmb.valor = int(self.ambiente)
        S1000.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        S1000.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1000.evento.ideEmpregador.tpInsc.valor = '1'
        S1000.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.origem.cnpj_cpf)[0:8]

        # Popula infoEmpregador
        S1000.evento.infoEmpregador.operacao = 'I'
        S1000.evento.infoEmpregador.idePeriodo.iniValid.valor = self.origem.esocial_periodo_id.code[
                                                                3:7] + '-' + self.origem.esocial_periodo_id.code[0:2]

        # Popula infoEmpregador.InfoCadastro
        S1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = self.origem.legal_name
        S1000.evento.infoEmpregador.infoCadastro.classTrib.valor = self.origem.classificacao_tributaria_id.codigo
        S1000.evento.infoEmpregador.infoCadastro.natJurid.valor = limpa_formatacao(
            self.origem.natureza_juridica_id.codigo)
        S1000.evento.infoEmpregador.infoCadastro.indCoop.valor = self.origem.ind_coop
        S1000.evento.infoEmpregador.infoCadastro.indConstr.valor = self.origem.ind_constr
        S1000.evento.infoEmpregador.infoCadastro.indDesFolha.valor = self.origem.ind_desoneracao
        S1000.evento.infoEmpregador.infoCadastro.indOptRegEletron.valor = self.origem.ind_opt_reg_eletron
        S1000.evento.infoEmpregador.infoCadastro.indEntEd.valor = self.origem.ind_ent_ed
        S1000.evento.infoEmpregador.infoCadastro.indEtt.valor = self.origem.ind_ett
        if self.origem.nr_reg_ett:
            S1000.evento.infoEmpregador.infoCadastro.nrRegEtt.valor = self.origem.nr_reg_ett
        if self.limpar_db:
            S1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = 'RemoverEmpregadorDaBaseDeDadosDaProducaoRestrita'
            S1000.evento.infoEmpregador.infoCadastro.classTrib.valor = '00'

        # Popula infoEmpregador.Infocadastro.contato
        S1000.evento.infoEmpregador.infoCadastro.contato.nmCtt.valor = self.origem.esocial_nm_ctt
        S1000.evento.infoEmpregador.infoCadastro.contato.cpfCtt.valor = self.origem.esocial_cpf_ctt
        S1000.evento.infoEmpregador.infoCadastro.contato.foneFixo.valor = limpa_formatacao(
            self.origem.esocial_fone_fixo)
        if self.origem.esocial_fone_cel:
            S1000.evento.infoEmpregador.infoCadastro.contato.foneCel.valor = limpa_formatacao(
                self.origem.esocial_fone_cel)
        if self.origem.esocial_email:
            S1000.evento.infoEmpregador.infoCadastro.contato.email.valor = self.origem.esocial_email

        # Popula infoEmpregador.infoCadastro.infoComplementares.situacaoPJ
        S1000.evento.infoEmpregador.infoCadastro.indSitPJ.valor = self.origem.ind_sitpj

        # Gera o ID do evento
        S1000.gera_id_evento(datetime.now().strftime('%Y%m%d%H%M%S'))
        data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.data_hora_transmissao = data_hora_transmissao

        # Grava o ID gerado
        self.id_evento = S1000.evento.Id.valor

        # Grava o XML gerado
        if self.envio_xml_id:
            envio = self.consulta_xml_id
            envio.consulta_xml_id = False
            envio.unlink()
        envio_xml = S1000.evento.xml
        envio_xml_nome = self.id_evento + '-envio.xml'
        anexo_id = self._grava_anexo(envio_xml_nome, envio_xml)
        self.envio_xml_id = anexo_id

        return S1000
