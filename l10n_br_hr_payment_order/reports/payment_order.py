# -*- coding: utf-8 -*-
from openerp.addons.account_payment.report.payment_order import payment_order


def _get_account_name(self, bank_id):
    if bank_id:
        # nome banco e numero da conta
        value_name = self.pool['res.partner.bank'].\
            name_get(self.cr, self.uid, [bank_id])
        # agencia
        bra_number = self.pool['res.partner.bank'].browse(
            self.cr, self.uid, bank_id).bra_number
        # digito
        bra_number_dig = self.pool['res.partner.bank'].browse(
            self.cr, self.uid, bank_id).bra_number_dig
        if value_name:
        # retorna BANCO .: 9999/99999-9
            return '{}-{}'.format(str(value_name[0][1]).replace(
                ': ', ': {}/'.format(bra_number)), bra_number_dig)
    return False


payment_order._get_account_name = _get_account_name
