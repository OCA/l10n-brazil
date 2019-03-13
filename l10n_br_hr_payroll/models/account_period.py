from openerp import api, models, fields


class L10nBrHrAccountPeriod(models.Model):
    _inherit = 'account.period'

    acordo_coletivo_id = fields.Many2one(
        string='Acordo Coletivo',
        comodel_name='l10n.br.hr.acordo.coletivo',
    )
