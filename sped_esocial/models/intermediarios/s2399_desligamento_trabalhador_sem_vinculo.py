# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
import pysped


class SpedHrRescisaoAutonomo(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.rescisao.autonomo"

    name = fields.Char(
        string='name',
        compute='_compute_display_name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_contract_id = fields.Many2one(
        string='Contrato',
        comodel_name='hr.contract',
    )
    sped_hr_rescisao_id = fields.Many2one(
        string="Rescisão Trabalhista",
        comodel_name="hr.payslip",
    )
    sped_s2399_registro_inclusao = fields.Many2one(
        string='Registro S-2399',
        comodel_name='sped.registro',
    )
    sped_s2399_registro_retificacao = fields.Many2many(
        string='Registro S-2399 - Retificação',
        comodel_name='sped.registro',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    situacao_esocial = fields.Selection(
        string='Situação no e-Social',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        compute="compute_situacao_esocial",
        store=True,
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )
    pagamento_pensao = fields.Boolean(
        string='Funcionário paga pensão?',
    )
    pens_alim = fields.Selection(
        string='Pensão Alimentícia',
        selection=[
            ('0', 'Não existe Pensão'),
            ('1', 'Percentual de Pensão'),
            ('2', 'Valor de Pensão'),
            ('3', 'Percentual e Valor de Pensão'),
        ],
        # required=True,
        help='e-Social: S2399 - pensAlim'
    )
    perc_aliment = fields.Float(
        string='Percentual da Pensão',
        help='e-Social: S2399 - percAliment',
    )
    vr_alim = fields.Float(
        string='Valor da Pensão',
        help='e-Social: S2399 - vrAlim'
    )
    s5001_id = fields.Many2one(
        string='S-5001 (Contribuições Sociais)',
        comodel_name='sped.contribuicao.inss',
    )

    @api.depends('sped_s2399_registro_inclusao.situacao',
                 'sped_s2399_registro_retificacao.situacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for desligamento in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if desligamento.sped_s2399_registro_inclusao and \
                    desligamento.sped_s2399_registro_inclusao.situacao == '4':
                ultima_atualizacao = \
                    desligamento.sped_s2399_registro_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for retificacao in desligamento.sped_s2399_registro_retificacao:
                if retificacao.situacao == '4':
                    if retificacao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = retificacao.data_hora_origem

            # Popula o campo na tabela
            desligamento.ultima_atualizacao = ultima_atualizacao

    @api.depends('sped_s2399_registro_inclusao.situacao',
                 'sped_s2399_registro_retificacao.situacao')
    def compute_situacao_esocial(self):
        for desligamento in self:
            situacao_esocial = '1'

            if desligamento.sped_s2399_registro_inclusao:
                situacao_esocial = \
                    desligamento.sped_s2399_registro_inclusao.situacao

            for retificao in desligamento.sped_s2399_registro_retificacao:
                situacao_esocial = retificao.situacao

            # Popula na tabela
            desligamento.situacao_esocial = situacao_esocial

    @api.multi
    def gerar_registro(self):
        if self.sped_hr_rescisao_id:
            origem = ('hr.payslip,%s' % self.sped_hr_rescisao_id.id)
        else:
            origem = ('hr.contract,%s' % self.hr_contract_id.id)
        values = {
            'tipo': 'esocial',
            'registro': 'S-2399',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtTSVTermino',
            'origem': origem,
            'origem_intermediario': (
                    'sped.hr.rescisao.autonomo,%s' % self.id),
        }
        if not self.sped_s2399_registro_inclusao:
            # Cria o registro de envio
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_s2399_registro_inclusao = sped_inclusao
        elif self.precisa_atualizar:
            # Cria o registro de Retificação
            values['operacao'] = 'R'
            sped_retificacao = self.env['sped.registro'].create(values)
            self.sped_s2399_registro_retificacao = [(4, sped_retificacao.id)]

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2399 - Desligamento {}'.format(
                record.sped_hr_rescisao_id.contract_id.display_name)

    @api.multi
    def create_sped_registro(self):
        """
        """
        sped_registro_id = self.env['sped.registro'].create({
            'tipo': 'esocial',
            'registro':'S-2399',
            'evento': 'evtTSVTermino',
            'company_id': self.sped_hr_rescisao_id.company_id.id,
            'ambiente': self.sped_hr_rescisao_id.company_id.esocial_tpAmb,
            'origem_intermediario': ("{},{}".format(self._name, self.id)),
            'origem':
                ("hr.payslip.autonomo,{}".format(self.sped_hr_rescisao_id.id)),
        })
        self.sped_s2399_registro_inclusao = sped_registro_id
        return sped_registro_id

    def get_registro_para_retificar(self, sped_registro):
        """
        Identificar o registro para retificar
        :return:
        """
        # Se tiver registro de retificação com erro ou nao possuir nenhuma
        # retificação ainda, retornar o registro que veio no parametro
        retificacao_com_erro = sped_registro.retificacao_ids.filtered(
            lambda x: x.situacao in ['1', '3'])
        if retificacao_com_erro or not sped_registro.retificacao_ids:
            return sped_registro

        # Do contrario navegar ate as retificacoes com sucesso e efetuar a
        # verificacao de erro novamente
        else:
            registro_com_sucesso = sped_registro.retificacao_ids.filtered(
                lambda x: x.situacao not in ['1', '3'])

            return self.get_registro_para_retificar(registro_com_sucesso[0])

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente ao desligamento de
        um contrato de trabalho sem vinculo
        """

        # Validação
        validacao = ""

        # Cria o registro
        S2399 = pysped.esocial.leiaute.S2399_2()

        #
        S2399.tpInsc = '1'
        S2399.nrInsc = limpa_formatacao(
            self.hr_contract_id.company_id.cnpj_cpf
        )[0:8]
        S2399.evento.ideEvento.tpAmb.valor = int(
            self.hr_contract_id.company_id.esocial_tpAmb
        )

        # Registro Original
        indRetif = '1'

        # Se for uma retificação
        if operacao == 'R':
            indRetif = '2'

            registro_para_retificar = self.get_registro_para_retificar(
                self.sped_s2399_registro_inclusao)

            S2399.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo

        S2399.evento.ideEvento.indRetif.valor = indRetif

        # Processo de Emissão = Aplicativo do Contribuinte
        S2399.evento.ideEvento.procEmi.valor = '1'
        S2399.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2399.evento.ideEmpregador.tpInsc.valor = '1'
        S2399.evento.ideEmpregador.nrInsc.valor = \
            limpa_formatacao(
                self.sped_hr_rescisao_id.company_id.cnpj_cpf or
                self.company_id.cnpj_cpf)[0:8]

        # evtTSVTermino.ideTrabSemVinculo
        employee_id = self.sped_hr_rescisao_id.contract_id.employee_id or self.hr_contract_id.employee_id
        S2399.evento.ideTrabSemVinculo.cpfTrab.valor = \
            limpa_formatacao(employee_id.cpf)
        S2399.evento.ideTrabSemVinculo.nisTrab.valor = \
            limpa_formatacao(employee_id.pis_pasep)
        S2399.evento.ideTrabSemVinculo.codCateg.valor = \
            self.hr_contract_id.category_id.code

        # evtTSVTermino.infoTSVTermino
        rescisao_id = self.sped_hr_rescisao_id
        S2399.evento.infoTSVTermino.dtTerm.valor = self.hr_contract_id.date_end
        if rescisao_id.contract_id.category_id.code in ['721', '722', '410']:

            if rescisao_id.contract_id.category_id.code in ['721']:
                S2399.evento.infoTSVTermino.mtvDesligTSV.valor = \
                    rescisao_id.mtv_deslig_esocial.codigo

            # evtTSVTermino.infoTSVTermino.VerbasResc
            verba_rescisoria = pysped.esocial.leiaute.S2399_VerbasResc_2()

            # evtTSVTermino.infoTSVTermino.VerbasResc.DmDev
            dm_dev = pysped.esocial.leiaute.S2399_DmDev_2()
            dm_dev.ideDmDev.valor = self.sped_hr_rescisao_id.number

            # evtTSVTermino.infoTSVTermino.VerbasResc.DmDev.ideEstabLot
            ide_estab_lot = pysped.esocial.leiaute.S2399_IdeEstabLot_2()
            ide_estab_lot.tpInsc.valor = '1'
            ide_estab_lot.nrInsc.valor = \
                limpa_formatacao(rescisao_id.company_id.cnpj_cpf)
            ide_estab_lot.codLotacao.valor = \
                rescisao_id.company_id.cod_lotacao

            # Verbas rescisórias do trabalhador
            for rubrica_line in rescisao_id.line_ids:
                if rubrica_line.salary_rule_id.category_id.id in (
                        self.env.ref('hr_payroll.PROVENTO').id,
                        self.env.ref('hr_payroll.DEDUCAO').id
                ):
                    if rubrica_line.salary_rule_id.code != 'PENSAO_ALIMENTICIA':
                        if rubrica_line.total > 0:

                            det_verbas = \
                                pysped.esocial.leiaute.S2399_DetVerbas_2()
                            det_verbas.codRubr.valor = \
                                rubrica_line.salary_rule_id.codigo
                            det_verbas.ideTabRubr.valor = \
                                rubrica_line.salary_rule_id.identificador
                            # det_verbas.qtdRubr.valor = ''
                            # det_verbas.fatorRubr.valor = ''
                            # det_verbas.vrunit.valor = ''
                            det_verbas.vrRubr.valor = str(rubrica_line.total)
                            ide_estab_lot.detVerbas.append(det_verbas)

            # evtTSVAltContr.infoTSVTermino.VerbasResc.DmDev.
            # ideEstabLot.InfoAgNocivo
            if rescisao_id.contract_id.category_id.code in ['738','731','734']:
                info_ag_nocivo = pysped.esocial.leiaute.S2399_InfoAgNocivo_2()
                info_ag_nocivo.grauExp.valor = 1
                ide_estab_lot.infoAgNocivo.append(info_ag_nocivo)

            # relacionando as classes
            dm_dev.ideEstabLot.append(ide_estab_lot)
            verba_rescisoria.dmDev.append(dm_dev)

            # Preencher outros vinculos
            outros_vinculos = \
                self.sped_hr_rescisao_id.contract_id.contribuicao_inss_ids

            periodo_rescisao = '{:02}/{}'.format(
                self.sped_hr_rescisao_id.mes_do_ano,
                self.sped_hr_rescisao_id.ano
            )

            for vinculo in outros_vinculos:
                if not periodo_rescisao == vinculo.period_id.code:
                    continue
                info_mv = pysped.esocial.leiaute.S2399_InfoMV_2()

                remun_outr_empr = \
                    pysped.esocial.leiaute.S2399_RemunOutrEmpr_2()
                remun_outr_empr.tpInsc.valor = \
                    vinculo.tipo_inscricao_vinculo
                remun_outr_empr.nrInsc.valor = limpa_formatacao(
                    vinculo.cnpj_cpf_vinculo)
                remun_outr_empr.codCateg.valor = \
                    vinculo.cod_categ_vinculo
                remun_outr_empr.vlrRemunOE.valor = \
                    vinculo.valor_remuneracao_vinculo

                info_mv.remunOutrEmpr.append(remun_outr_empr)

                if vinculo.valor_alicota_vinculo >= 642.33:
                    info_mv.indMV.valor = '3'
                else:
                    info_mv.indMV.valor = '2'

                verba_rescisoria.infoMV.append(info_mv)

            S2399.evento.infoTSVTermino.verbasResc.append(verba_rescisoria)

        return S2399, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        if evento:
            for tot in evento.tot:

                if tot.tipo.valor == 'S5001':

                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-2399'),
                        ('recibo', '=', tot.eSocial.evento.ideEvento.nrRecArqBase.valor),
                    ])

                    # Busca pelo sped.registro deste totalizador (se ele já existir)
                    sped_s5001 = self.env['sped.registro'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Busca pelo registro intermediário (se ele já existir)
                    sped_intermediario = self.env['sped.contribuicao.inss'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Popula os valores para criar/alterar o registro intermediário do totalizador
                    vals_intermediario_totalizador = {
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'periodo_id': sped_registro.origem_intermediario.periodo_id.id,
                        'trabalhador_id': self.sped_hr_rescisao_id.employee_id.id,
                        'sped_registro_s2399': sped_registro.id,
                    }

                    # Cria/Altera o registro intermediário
                    if sped_intermediario:
                        sped_intermediario.write(vals_intermediario_totalizador)
                    else:
                        sped_intermediario = self.env[
                            'sped.contribuicao.inss'].create(
                            vals_intermediario_totalizador)

                    # Popula os valores para criar/alterar o sped.registro do totalizador
                    vals_registro_totalizador = {
                        'tipo': 'esocial',
                        'registro': 'S-5001',
                        'evento': 'evtBasesTrab',
                        'operacao': 'na',
                        'ambiente': sped_registro.ambiente,
                        'origem': (
                                    'sped.contribuicao.inss,%s' % sped_intermediario.id),
                        'origem_intermediario': (
                                    'sped.contribuicao.inss,%s' % sped_intermediario.id),
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'situacao': '4',
                        'recibo': tot.eSocial.evento.ideEvento.nrRecArqBase.valor,
                    }

                    # Cria/Altera o sped.registro do totalizador
                    if sped_s5001:
                        sped_s5001.write(vals_registro_totalizador)
                    else:
                        sped_s5001 = self.env['sped.registro'].create(
                            vals_registro_totalizador)

                    # Popula o intermediário totalizador com o registro totalizador
                    sped_intermediario.sped_registro_s5001 = sped_s5001

                    # Popula o intermediário S2399 com o intermediário totalizador
                    self.s5001_id = sped_intermediario

                    # Popula o intermediario do registro enviado com o
                    # totalizador obtido
                    sped_registro.sped_s5001 = sped_intermediario

                    # Popula o XML em anexo no sped.registro totalizador
                    if sped_s5001.consulta_xml_id:
                        consulta = sped_s5001.consulta_xml_id
                        sped_s5001.consulta_xml_id = False
                        consulta.unlink()
                    consulta_xml = tot.eSocial.xml
                    consulta_xml_nome = sped_s5001.id_evento + '-consulta.xml'
                    anexo_id = sped_registro._grava_anexo(consulta_xml_nome,
                                                          consulta_xml)
                    sped_s5001.consulta_xml_id = anexo_id

                    # Limpa a tabela sped.contribuicao.inss.infocpcal
                    for receita in sped_intermediario.infocpcalc_ids:
                        receita.unlink()

                    # Limpa a tabela sped.contribuicao.inss.ideestablot
                    for base in sped_intermediario.ideestablot_ids:
                        base.unlink()

                    # Popula a tabela sped.contribuicao.inss.infocpcal com os valores apurados no S-5001
                    for receita in tot.eSocial.evento.infoCpCalc:
                        vals = {
                            'parent_id': sped_intermediario.id,
                            'tp_cr': receita.tpCR.valor,
                            'vr_cp_seg': float(receita.vrCpSeg.valor),
                            'vr_desc_seg': float(receita.vrDescSeg.valor),
                        }
                        self.env['sped.contribuicao.inss.infocpcalc'].create(
                            vals)

                    # Popula a tabela sped.contribuicao.inss.ideestablot
                    for estabelecimento in tot.eSocial.evento.infoCp.ideEstabLot:
                        for categoria in estabelecimento.infoCategIncid:
                            for base in categoria.infoBaseCS:
                                vals = {
                                    'parent_id': sped_intermediario.id,
                                    'tp_insc': estabelecimento.tpInsc.valor,
                                    'nr_insc': estabelecimento.nrInsc.valor,
                                    'cod_lotacao': estabelecimento.codLotacao.valor,
                                    'matricula': categoria.matricula.valor,
                                    'cod_categ': categoria.codCateg.valor,
                                    'ind13': base.ind13.valor,
                                    'tp_valor': base.tpValor.valor,
                                    'valor': float(base.valor.valor),
                                }
                                if categoria.indSimples:
                                    vals['ind_simples'] = categoria.indSimples.valor
                                self.env['sped.contribuicao.inss.ideestablot'].create(vals)

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.sped_hr_rescisao_id.contract_id.employee_id
