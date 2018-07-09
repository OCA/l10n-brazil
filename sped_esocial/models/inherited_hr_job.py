# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class HrJob(models.Model):

    _inherit = 'hr.job'
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'Este Código e-Social já existe !'),
    ]

    # Campos de controle S-1030
    sped_cargo_id = fields.Many2one(
        string='SPED Cargo',
        comodel_name='sped.esocial.cargo',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        related='sped_cargo_id.situacao_esocial',
        readonly=True,
    )

    codigo = fields.Char(
        string='Código',
        size=30,
    )
    ini_valid = fields.Many2one(
        string='Válido desde',
        comodel_name='account.period',
    )
    fim_valid = fields.Many2one(
        string='Válido até',
        comodel_name='account.period',
    )
    cargo_publico = fields.Boolean(
        string='É cargo Público',
    )
    acum_cargo = fields.Selection(
        string='Acúmulo de Cargo Público',
        selection=[
            ('1', '1-Não acumulável'),
            ('2', '2-Profissional de Saúde'),
            ('3', '3-Professor'),
            ('4', '4-Técnico/Científico'),
        ],
    )
    contagem_esp = fields.Selection(
        string='Código de Contagem de tempo Especial',
        selection=[
            ('1', 'Não'),
            ('2', 'Professor (Infantil, Fundamental e Médio'),
            ('3', 'Professor de Ensino Superior, Magistrado, Membro de Ministério Público, Membro de Tribunal de Contas (com ingresso anterior a 16/12/1998 EC nr. 20/98)'),
            ('4', 'Atividade de risco'),
        ],
    )
    dedic_excl = fields.Selection(
        string='Cargo de Dedicação Exclusiva',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    nr_lei = fields.Char(
        string='Nº Lei que criou o cargo',
        size=12,
    )
    dt_lei = fields.Date(
        string='Data da Lei',
    )
    sit_cargo = fields.Selection(
        string='Situação gerada pela Lei.',
        selection=[
            ('1', '1-Criação'),
            ('2', '2-Extinção'),
            ('3', '3-Reestruturação'),
        ],
    )
