# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields, _


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
    trct_name= fields.Char('TRCT Name')
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


