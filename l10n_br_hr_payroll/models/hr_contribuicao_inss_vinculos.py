# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp import exceptions


class HrContribuicaoInssVinculos(models.Model):
    _name = "hr.contribuicao.inss.vinculos"

    contrato_id = fields.Many2one(
        string='Contrato',
        comodel_name='hr.contract',
        required=True,
    )
    tipo_inscricao_vinculo = fields.Selection(
        string='Tipo do Vínculo',
        selection=[
            ('1', 'CNPJ'),
            ('2', 'CPF'),
        ],
        required=True,
        help='e-Social: S-2299 - tpInsc',
    )
    cnpj_cpf_vinculo = fields.Char(
        string='CNPJ/CPF Vínculo',
        required=True,
        size=17,
        help='e-Social: S-2299 - nrInsc',
    )
    cod_categ_vinculo = fields.Char(
        string='Cód Categoria',
        size=3,
        required=True,
    )
    valor_remuneracao_vinculo = fields.Float(
        string='Remuneração Bruto',
        required=True,
        help='e-Social: S-2299 - vlrRemunOE'
    )
    valor_alicota_vinculo = fields.Float(
        string='Valor Pago',
        compute='_compute_valor_aliquota_vinculo',
    )
    period_id = fields.Many2one(
        string='Competência',
        comodel_name='account.period',
        required=True,
    )

    @api.model
    def create(self, vals):
        self._valida_valores_unicos(vals)
        return super(HrContribuicaoInssVinculos, self).create(vals)

    @api.multi
    def write(self, vals):
        self._valida_valores_unicos(vals)
        return super(HrContribuicaoInssVinculos, self).write(vals)

    @api.multi
    def _valida_valores_unicos(self, vals):
        domain = [
            (
                'cnpj_cpf_vinculo', '=',
                vals.get('cnpj_cpf_vinculo') or self.cnpj_cpf_vinculo
            ),
            ('period_id', '=', vals.get('period_id') or self.period_id.id),
        ]
        vinculo_ids = self.search(domain)
        if vinculo_ids:
            raise exceptions.Warning(
                'Só é possível uma entrada por vínculo no período selecionado!'
            )

    @api.onchange('employee_id')
    def onchange_funcionario(self):
        """
        COnfigurar o tipo do contrato de acordo com o tipo de vinculo do
        funcionario
        """
        for record in self:
            if record.employee_id:
                record.tipo = record.employee_id.tipo

    @api.constrains('categoria')
    def constrains_categoria(self):
        """
        Validar categoria do contrato para o esocial
        :return:
        """
        categoria_autonomos = \
            [201, 202, 305, 308, 401, 410, 701, 711, 712, 721, 722, 723, 731,
             734, 738, 741, 751, 761, 771, 781, 901, 902, 903, 904, 905]

        if self.tipo == 'autonomo' and \
                self.categoria not in categoria_autonomos:
                raise exceptions.Warning(
                    'Categoria inválida para Contratos de autônomos.')

    @api.depends('valor_remuneracao_vinculo', 'period_id')
    def _compute_valor_aliquota_vinculo(self):
        for record in self:
            valor_aliquota = 0

            if record.period_id and record.valor_remuneracao_vinculo:
                valor_aliquota, reference = \
                    self.env['l10n_br.hr.social.security.tax']._compute_inss(
                        record.valor_remuneracao_vinculo,
                        record.period_id.date_start
                    )

            record.valor_alicota_vinculo = valor_aliquota
