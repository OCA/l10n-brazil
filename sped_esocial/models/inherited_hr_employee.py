# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Cria campos pais_nac_id e pais_nascto_id para substituir o place_of_birth (que é texto)
    pais_nascto_id = fields.Many2one(
        string='País de Nascimento',
        comodel_name='sped.pais',
    )
    pais_nac_id = fields.Many2one(
        string='Nacionalidade',
        comodel_name='sped.pais',
    )

    # Dados que faltam em l10n_br_hr
    cnh_dt_exped = fields.Date(
        string='Data de Emissão',
    )
    cnh_uf = fields.Many2one(
        string='UF',
        comodel_name='res.country.state',
    )
    cnh_dt_pri_hab = fields.Date(
        string='Data da 1ª Hab.',
    )
    sped_esocial_alterar_cadastro_id = fields.Many2one(
        string='Alterar Cadastro',
        comodel_name='sped.esocial.alteracao.funcionario',
    )
    situacao_esocial_inicial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        related='contract_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        related='sped_esocial_alterar_cadastro_id.precisa_atualizar',
    )

    @api.multi
    def write(self, vals):
        self._gerar_tabela_intermediaria_alteracao(vals)
        return super(HrEmployee, self).write(vals)

    @api.multi
    def _gerar_tabela_intermediaria_alteracao(self, vals={}):
        # Se o registro intermediário do S-2205 não existe, criá-lo
        if not self.sped_esocial_alterar_cadastro_id and not \
                vals.get('sped_esocial_alterar_cadastro_id'):
            matriz = self.company_id.id if self.company_id.eh_empresa_base \
                else self.company_id.matriz.id
            self.sped_esocial_alterar_cadastro_id = \
                self.env['sped.esocial.alteracao.funcionario'].create(
                    {
                        'company_id': matriz,
                        'hr_employee_id': self.id,
                    }
                )

    @api.multi
    def atualizar_cadastro_funcionario(self):
        self.ensure_one()

        self._gerar_tabela_intermediaria_alteracao()

        # Processa cada tipo de operação do S-2205
        # O que realmente precisará ser feito é
        # tratado no método do registro intermediário
        self.sped_esocial_alterar_cadastro_id.gerar_registro()
