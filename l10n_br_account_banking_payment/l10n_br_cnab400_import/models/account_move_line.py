from openerp import models, fields


class AccounMoveLine(models.Model):
    _inherit = "account.move.line"

    cnab_move_ids = fields.One2many(
        'l10n_br_cnab.move', 'move_line_id', u'Detalhes de retorno CNAB')
    ml_identificacao_titulo_no_banco = fields.Char(
        u'Identifica??o do t?tulo no banco')

    str_ocorrencia = fields.Char(u'Identifica??o de Ocorr?ncia')
    str_motiv_a = fields.Char(u'Motivo da ocorr?ncia 01')
    str_motiv_b = fields.Char(u'Motivo de ocorr?ncia 02')
    str_motiv_c = fields.Char(u'Motivo de ocorr?ncia 03')
    str_motiv_d = fields.Char(u'Motivo de ocorr?ncia 04')
    str_motiv_e = fields.Char(u'Motivo de ocorr?ncia 05')
