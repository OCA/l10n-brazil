# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - http://www.abgf.gov.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.exceptions import ValidationError

TIPO_SITUACAO = [
    ('A', 'A - Acordo Coletivo de Trabalho'),
    ('B', 'B - Legislação federal, estadual, municipal ou distrital'),
    ('C', 'C - Convenção Coletiva de Trabalho'),
    ('D', 'D - Sentença Normativa - Dissídio'),
    ('E', 'E - Conversão de Licença Saúde em Acidente de Trabalho'),
    ('F', 'F - Outras verbas de natureza salarial ou não salarial devidas '
          'após o desligamento'),
    ('G', 'G - Antecipação de diferenças de Acordo, '
          'Convenção ou Dissídio Coletivo.'),
]

class HrPaylisp(models.Model):
    _inherit = "hr.payslip"

    # Campo motificado para utilizar a tabela de campos do e-Social
    # Tabela 19 - Motivos de Desligamento
    mtv_deslig_esocial = fields.Many2one(
        string='Motivo Desligamento',
        comodel_name='sped.motivo_desligamento',
        help="e-Social: S-2299 - mtvDeslig"
    )

    sped_s2299 = fields.Many2one(
        string='Registro SPED S-2299',
        comodel_name='sped.hr.rescisao',
    )

    sped_s2399 = fields.Many2one(
        string='Registro SPED S-2399',
        comodel_name='sped.hr.rescisao.autonomo',
    )

    situacao_esocial_s2299 = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação no e-Social',
        related='sped_s2299.situacao_s2299',
        readonly=True,
    )

    # sped_s2399 = fields.Many2one(
    #     string='Registro SPED S-2399',
    #     comodel_name='sped.hr.rescisao.autonomo',
    # )
    sped_remuneracao_id = fields.One2many(
        string = u'Sped Remuneração (Intermediario)',
        comodel_name = 'sped.esocial.remuneracao',
        inverse_name = 'payslip_ids',
    )

    sped_pagamento_id = fields.One2many(
        string = u'Sped Pagamento (Intermediario)',
        comodel_name = 'sped.esocial.pagamento',
        inverse_name = 'payslip_ids',
    )

    tipo_situacao = fields.Selection(
        selection=TIPO_SITUACAO,
        string=u'Tipo da Situação',
        help=u'e-Social S-1200 tpAcConv: Tipo do instrumento ou situação '
             u'ensejadora da remuneração relativa a Períodos de '
             u'Apuração Anteriores'
    )

    descricao_situacao = fields.Char(
        string=u'Descrição da Situação',
        help=u'e-Social: S-1200 dsc: Descrição do instrumento ou situação '
             u'que originou o pagamento das verbas relativas a '
             u'períodos anteriores.',
    )

    remuneracao_sucessora = fields.Selection(
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
        string=u'Verbas de Natureza Salarial?',
        help=u'e-Social: S-1200 remunSuc: Indicar se a remuneração é relativa'
             u' a verbas de natureza salarial ou não salarial devidas pela '
             u'empresa sucessora a empregados desligados ainda na sucedida',
        default='N',
    )

    @api.multi
    def hr_verify_sheet(self):
        for holerite in self:
            if holerite.state == 'draft':
                if holerite.tipo_de_folha == 'rescisao':
                    holerite.contract_id.resignation_cause_id = \
                        holerite.mtv_deslig_esocial
                    holerite.contract_id.resignation_date = \
                        holerite.data_afastamento
            super(HrPaylisp, holerite).hr_verify_sheet()

    @api.model
    def create(self, vals):
        if vals.get('mtv_deslig_esocial'):
            vals['mtv_deslig'] = self.retorna_motivo_desligamento(vals['mtv_deslig_esocial'])

        return super(HrPaylisp, self).create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            if vals.get('mtv_deslig_esocial'):
                vals['mtv_deslig'] = record.retorna_motivo_desligamento(vals['mtv_deslig_esocial'])
            super(HrPaylisp, record).write(vals)

        return True

    def retorna_motivo_desligamento(self, motivo_id):
        """
        Função responsável por retornor o código e a descrição do motivo de desligamento por extenso através do
        id do motivo.
        """
        mtv_desligamento_esocial = self.env['sped.motivo_desligamento'].browse(motivo_id)

        return '{}-{}'.format(mtv_desligamento_esocial.codigo, mtv_desligamento_esocial.nome)

    def INSS(self, BASE_INSS):
        base_inss_vinculos = 0

        if BASE_INSS:
            base_inss_vinculos = self.get_base_inss_vinculos()

        inss, aliquota = super(HrPaylisp, self).INSS(
            BASE_INSS + base_inss_vinculos)

        if BASE_INSS:
            inss -= self.get_inss_vinculos(base_inss_vinculos, aliquota)

        return inss, aliquota

    def get_base_inss_vinculos(self):
        base_inss_vinculos = 0
        if self.contract_id.contribuicao_inss_ids:
            period_id = self.env['account.period'].find(self.date_from)
            vinculos = self.env['hr.contribuicao.inss.vinculos'].search([
                ('contrato_id', '=', self.contract_id.id),
                ('period_id', '=', period_id.id),
            ])

            for vinculo in vinculos:
                base_inss_vinculos += vinculo.valor_remuneracao_vinculo

        return base_inss_vinculos

    def get_inss_vinculos(self, BASE_INSS_VINCULOS, aliquota):
        inss_vinculos = 0
        if BASE_INSS_VINCULOS:
            inss_vinculos = BASE_INSS_VINCULOS * (aliquota / 100)

        return inss_vinculos

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.contract_id.employee_id

    @api.multi
    def ativar_remuneracao(self):
        """
        Gerar registros do esocial para remuneracao
        """
        for payslip in self:
            if payslip.state not in ['verify', 'done']:
                raise ValidationError(
                    "Existem Holerites não validados neste período !\n"
                    "Confirme ou Cancele todos os holerites deste período"
                    "antes de processar o e-Social.")


            # periodo = self.periodo_id
            matriz  = payslip.company_id
            trabalhador = payslip.employee_id
            period_id = self.env['account.period'].find(payslip.date_from)

            # Verifica se o registro S-1200 já existe, cria ou atualiza
            domain_s1200 = [
                ('company_id', '=', matriz.id),
                ('trabalhador_id', '=', trabalhador.id),
                ('periodo_id', '=', period_id.id),
            ]

            s1200 = self.env['sped.esocial.remuneracao'].search(domain_s1200)
            if not s1200:
                vals = {
                    'company_id': matriz.id,
                    'trabalhador_id': trabalhador.id,
                    'contract_ids': [(6, 0, payslip.contract_id.ids)],
                    'periodo_id': period_id.id,
                }

                # Criar intermediario de acordo com o tipo de employee
                if trabalhador.tipo != 'autonomo':
                    vals.update(
                        {'payslip_ids': [(6, 0, payslip.ids)]})
                else:
                    vals.update(
                        {'payslip_autonomo_ids': [(6, 0, payslip.ids)]})


                # Relaciona o s1200 com o período do e-Social
                sped_esocial = self.env['sped.esocial'].search([
                    ('periodo_id','=',period_id.id)
                ], limit=1)

                if sped_esocial:

                    s1200 = self.env['sped.esocial.remuneracao'].create(vals)

                    sped_esocial.remuneracao_ids = [(4, s1200.id)]

                else:
                    raise ValidationError(
                        "Nenhum período do esocial encontrado.")

                # Cria o registro de transmissão sped (se ainda não existir)
                s1200.atualizar_esocial()

    @api.multi
    def ativar_pagamento(self):
        """
        Gerar registros do esocial para remuneracao
        """
        for payslip in self:

            if payslip.state not in ['verify', 'done']:
                raise ValidationError(
                    "Existem Holerites não validados neste período !\n"
                    "Confirme ou Cancele todos os holerites deste período"
                    "antes de processar o e-Social.")

            matriz  = payslip.company_id
            trabalhador = payslip.employee_id
            period_id = self.env['account.period'].find(payslip.date_from)

            domain_s1210 = [
                ('company_id', '=', matriz.id),
                ('beneficiario_id', '=', trabalhador.id),
                ('periodo_id', '=', period_id.id),
            ]

            s1210 = self.env['sped.esocial.pagamento'].search(domain_s1210)

            if not s1210:
                vals = {
                    'company_id': matriz.id,
                    'beneficiario_id': trabalhador.id,
                    'periodo_id': period_id.id,
                    'contract_ids': [(6, 0, payslip.contract_id.ids)],
                }

                # Criar intermediario de acordo com o tipo de employee
                if trabalhador.tipo != 'autonomo':
                    vals.update({'payslip_ids': [(6, 0, payslip.ids)]})
                else:
                    vals.update({'payslip_autonomo_ids': [(6, 0, payslip.ids)]})

                # Relaciona o s1200 com o período do e-Social
                sped_esocial = self.env['sped.esocial'].search([
                    ('periodo_id','=',period_id.id)
                ], limit=1)

                if sped_esocial:

                    s1210 = self.env['sped.esocial.pagamento'].create(vals)

                    sped_esocial.pagamento_ids = [(4, s1210.id)]

                    # Atualiza o registro de transmissão e a lista de registros
                    # S-1210 deste período
                    s1210.atualizar_esocial()

                else:
                    raise ValidationError(
                        "Nenhum período do esocial encontrado.")
