# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import models, api, _
from openerp.exceptions import Warning as UserError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.multi
    @api.constrains('bra_number')
    def check_bra_number(self):
        for record in self:
            # TODO - https://github.com/OCA/l10n-brazil/issues/588
            if record.bank.bic == '033':
                if len(record.bra_number) > 4:
                    raise UserError(_(
                        u'O cógido da Agencia Bancaria do Santander'
                        u' deve ter no máximo quatro caracteres.'
                    ))
