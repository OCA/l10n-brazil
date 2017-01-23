# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class L10nBrHrSyndicate(models.Model):
    _name = "l10n.br.hr.syndicate"
    _rec_name = 'syndicate'

    dissidio_month = fields.Selection(
        [
            ('jan', 'January'),
            ('feb', 'Febuary'),
            ('mar', 'March'),
            ('apr', 'April'),
            ('may', 'May'),
            ('jun', 'June'),
            ('jul', 'July'),
            ('ago', 'August'),
            ('sep', 'September'),
            ('oct', 'October'),
            ('nov', 'November'),
            ('dec', 'December')
        ],
        'Dissidio month',
        required=True
    )
    syndicate = fields.Char('Syndicate Name', required=True)
    trct_code = fields.Char('TRCT Code')
    trct_name = fields.Char('TRCT Name')
    syndicate_type = fields.Selection(
        [
            ('teste', 'Teste')
        ],
        'Syndicate Type',
        required=True
    )
    syndicate_entity = fields.Selection(
        [
            ('teste2', 'Teste2')
        ],
        'Syndicate Entity',
        required=True
    )
    collectives_conventions_ids = fields.Many2many(
        'l10n.br.hr.collectives.conventions',
        'l10n_br_hr_syndicate_conventions_rel', 'syndicate_id',
        'collectives_conventions_id',
        string='Collectives Conventions'
    )
    job_minimum_wage_ids = fields.Many2many(
        'l10n.br.hr.job.minimum.wage',
        'l10n_br_hr_syndicate_job_minimum_wage_rel', 'syndicate_id',
        'job_minimum_wage_id',
        string="Job Minimum Wage"
    )
    job_rubric_ids = fields.Many2many(
        'l10n.br.hr.job.rubric',
        'l10n_br_hr_syndicate_job_rubric_rel', 'syndicate_id',
        'job_rubric_id',
        string="Job Rubric"
    )
    job_fix_rubric_ids = fields.Many2many(
        'l10n.br.hr.job.fix.rubric',
        'l10n_br_hr_syndicate_job_fix_rubric_rel', 'syndicate_id',
        'job_fix_rubric_id',
        string="Job Fix Rubrics"
    )


class L10nBrHrCollectivesConventions(models.Model):
    _name = "l10n.br.hr.collectives.conventions"

    base_year = fields.Date('Base Year')
    agreement_date = fields.Date('Agreement Date')
    process_number = fields.Integer('Process Number')
    vara = fields.Char('Vara')
    agreement_type = fields.Char('Agreement Type')
    syndicate_ids = fields.Many2many(
        'l10n.br.hr.syndicate',
        'l10n_br_hr_syndicate_conventions_rel', 'collectives_conventions_id',
        'syndicate_id',
        string="Syndicates"
    )


class L10nBrHrJobMinimumWage(models.Model):
    _name = "l10n.br.hr.job.minimum.wage"

    job_id = fields.Many2one("hr.job", "Job")
    date_beginning = fields.Date("Date Beginning")
    preferential_workload = fields.Float("Preferential Workload")
    month_minimum_wage = fields.Float("Month Minimum Wage")
    hour_minimum_wage = fields.Float("Hour Minimum Wage")
    syndicate_ids = fields.Many2many(
        'l10n.br.hr.syndicate',
        'l10n_br_hr_syndicate_job_minimum_wage_rel', 'job_minimum_wage_id',
        'syndicate_id',
        string="Syndicates"
    )


class L10nBrHrJobRubric(models.Model):
    _name = "l10n.br.hr.job.rubric"

    rubric_id = fields.Many2one("hr.salary.rule", "Rubric")
    job_id = fields.Many2one("hr.job", "Job")
    data_beginning = fields.Date("Date Beginning")
    data_ending = fields.Date("Date Ending")
    reference = fields.Char("Reference")
    quantity = fields.Integer("Quantity")
    percentage = fields.Float("Percentage")
    value = fields.Float("Value")
    syndicate_ids = fields.Many2many(
        'l10n.br.hr.syndicate',
        'l10n_br_hr_syndicate_job_rubric_rel', 'job_rubric_id',
        'syndicate_id',
        string="Syndicates"
    )


class L10nBrHrJobFixRubric(models.Model):
    _name = "l10n.br.hr.job.fix.rubric"

    rubric_id = fields.Many2one("hr.salary.rule", "Rubric")
    monthly_hourly = fields.Many2one("hr.employee", "Mensalist/Hourly")
    initial_wage = fields.Float("Initial Wage")
    final_wage = fields.Float("Final Wage")
    date_beginning = fields.Date("Date Beginning")
    date_ending = fields.Date("Date Ending")
    reference = fields.Char("Reference")
    quantity = fields.Integer("Quantity")
    percentage = fields.Float("Percentage")
    value = fields.Float("Value")
    syndicate_ids = fields.Many2many(
        'l10n.br.hr.syndicate',
        'l10n_br_hr_syndicate_job_fix_rubric_rel', 'job_fix_rubric_id',
        'syndicate_id',
        string="Syndicates"
    )
