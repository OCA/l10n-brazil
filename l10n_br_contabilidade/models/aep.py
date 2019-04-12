# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp.addons.mis_builder.models.aep import AccountingExpressionProcessor

def get_account_reference(self, account_ids, account_depara_plano_id):
    """SELECT conta_sistema_id from account_mapeamento where
    account_depara_plano_id = 1 AND conta_referencia_id in (2294, 2298)"""

    sql_filters = {
        'conta_referencia_id': tuple(account_ids),
        'account_depara_plano_id': account_depara_plano_id,
    }

    sql_select = "SELECT adcs.conta_sistema_id " \
                 "FROM account_depara_conta_sistema_rel adcs " \
                 "RIGHT JOIN account_depara ad " \
                 "ON adcs.account_depara_id=ad.id"

    sql_where = "WHERE ad.conta_referencia_id IN  %(conta_referencia_id)s " \
                "AND ad.account_depara_plano_id = %(account_depara_plano_id)s"

    sql_order = "order by adcs.conta_sistema_id"

    sql = ' '.join((sql_select, sql_where, sql_order))
    self.env.cr.execute(sql, sql_filters)
    fetch_only_ids = self.env.cr.fetchall()
    if not fetch_only_ids:
        return []
    only_ids = [str(only_id[0]) for only_id in fetch_only_ids]
    return only_ids

def _load_account_codes(self, account_codes, root_account):
    """
    """
    # Se contas possuirem mapeamento no depara
    account_model = self.env['account.account']

    account_ids = account_model.search([
        ('code', 'in', list(account_codes)),
        ('parent_id', 'child_of', root_account.id),
    ])

    contas_referencia = set(get_account_reference(self, account_ids._ids, 1))

    if contas_referencia:
        account_codes = set(contas_referencia)

    # TODO: account_obj is necessary because _get_children_and_consol
    #       does not work in new API?
    account_obj = self.env.registry('account.account')
    exact_codes = set()
    like_codes = set()
    for account_code in account_codes:
        if account_code in self._account_ids_by_code:
            continue
        if account_code is None:
            # by convention the root account is keyed as
            # None in _account_ids_by_code, so it is consistent
            # with what _parse_match_object returns for an
            # empty list of account codes, ie [None]
            exact_codes.add(root_account.code)
        elif '%' in account_code:
            like_codes.add(account_code)
        else:
            exact_codes.add(account_code)
    for account in account_model. \
            search([('code', 'in', list(exact_codes)),
                    ('parent_id', 'child_of', root_account.id)]):
        if account.code == root_account.code:
            code = None
        else:
            code = account.code
        if account.type in ('view', 'consolidation'):
            self._account_ids_by_code[code].update(
                account_obj._get_children_and_consol(
                    self.env.cr, self.env.uid,
                    [account.id],
                    self.env.context))
        else:
            self._account_ids_by_code[code].add(account.id)
    for like_code in like_codes:
        for account in account_model. \
                search([('code', '=like', like_code),
                        ('parent_id', 'child_of', root_account.id)]):
            if account.type in ('view', 'consolidation'):
                self._account_ids_by_code[like_code].update(
                    account_obj._get_children_and_consol(
                        self.env.cr, self.env.uid,
                        [account.id],
                        self.env.context))
            else:
                self._account_ids_by_code[like_code].add(account.id)






AccountingExpressionProcessor._load_account_codes = _load_account_codes
