# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class SpedEsocialTurnosTrabalho(models.Model):
    _name = "esocial.turnos.trabalho"

    hr_entr = fields.Char(
        string="Horário de Entrada",
        required=True,
        size=5,
    )
    hr_saida = fields.Char(
        string="Horário de Saída",
        required=True,
        size=5,
    )
    horario_intervalo_ids = fields.Many2many(
        string="Intervalos",
        comodel_name="sped.esocial.turnos.intervalo",
        column1='turno_trabalho_id',
        column2='intervalo_id',
    )
    dur_jornada = fields.Char(
        string="Tempo de Duração",
        compute="_calcular_tempo_duracao_turno"
    )
    per_hor_flexivel = fields.Selection(
        string="Permite Flexibilidade?",
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ]
    )
    cod_hor_contrat = fields.Char(
        string="Código no e-Social",
        required=True,
        size=30,
    )
    ini_valid = fields.Char(
        string="Competência de início",
        required=True,
        size=7,
    )
    fim_valid = fields.Char(
        string="Competência final",
        size=7,
    )

    @api.multi
    def _calcular_tempo_duracao_turno(self):
        for record in self:
            record.dur_jornada = str(8*60)

    @api.multi
    def gerar_documento_sped(self):
        """
        
        :return: 
        """
        
        sped_turnos_obj = self.env['sped.esocial.turnos.trabalho']
        sped_esocial_obj = self.env['sped.esocial']
        company_id = self.env['res.company'].search([
            ('eh_empresa_base', '=', True),
        ], limit=1)
        sped_esocial_id = sped_esocial_obj.get_esocial_vigente(company_id)

        sped_turnos_obj.create({
            'esocial_id': sped_esocial_id.id,
            'sped_esocial_turnos_trabalho_id': self.id,
        })
        
        
class SpedEsocialTurnosIntervalo(models.Model):
    _name = "sped.esocial.turnos.intervalo"

    ini_interv = fields.Char(
        string="Horário de Início",
        required=True,
        size=5
    )
    term_interv = fields.Char(
        string="Horário de Fim",
        required=True,
        size=5
    )
    dur_interv = fields.Char(
        string="Duração",
        compute="_calcular_tempo_duracao_intervalo"
    )
    tp_interv = fields.Selection(
        string="Tipo de intervalo",
        selection=[
            ('1', 'Intervalo em horário fixo'),
            ('2', 'Intervalo em horário variável'),
        ]
    )

    @api.multi
    def _calcular_tempo_duracao_intervalo(self):
        for record in self:
            record.dur_interv = str(60)
