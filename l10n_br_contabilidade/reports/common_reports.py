# -*- coding: utf-8 -*-

# Livro Razão
from openerp.addons.account_financial_report_webkit.report.general_ledger \
    import CommonReportHeaderWebkit


# Livro Razão
def _get_move_line_datas(self, move_line_ids,
                         order='per.special DESC, l.date ASC, \
                             per.date_start ASC, m.name ASC'):
    """
        Livro Razão
        1 - Altera a query do método do core para trazer a narration e o número
            da sequencia;
        2 - Se a natureza da conta for Devedora, então o valor de balance deve
            ser "debito - crédito", se Credora será "crédito - debito"
    """

    if not move_line_ids:
        return []
    if not isinstance(move_line_ids, list):
        move_line_ids = [move_line_ids]
    monster = """
SELECT l.id AS id,
            l.date AS ldate,
            j.code AS jcode ,
            j.type AS jtype,
            l.currency_id,
            l.account_id,
            l.amount_currency,
            l.ref AS lref,
            l.name AS lname,
            CASE
                WHEN LEFT(an.name, 1) = 'D' THEN
                    COALESCE(l.debit, 0.0) - COALESCE(l.credit, 0.0)
                ELSE
                    COALESCE(l.credit, 0.0) - COALESCE(l.debit, 0.0)
            END AS balance,
            l.debit,
            l.credit,
            l.period_id AS lperiod_id,
            per.code as period_code,
            per.special AS peropen,
            l.partner_id AS lpartner_id,
            p.name AS partner_name,
            m.name AS move_name,
            COALESCE(partialrec.name, fullrec.name, '') AS rec_name,
            COALESCE(partialrec.id, fullrec.id, NULL) AS rec_id,
            m.id AS move_id,
            c.name AS currency_code,
            i.id AS invoice_id,
            i.type AS invoice_type,
            i.number AS invoice_number,
            l.date_maturity,
            m.narration,
            m.sequencia,
            LEFT(an.name, 1) AS natureza
FROM account_move_line l
    JOIN account_move m on (l.move_id=m.id)
    INNER JOIN account_account aa on (l.account_id = aa.id)
    INNER JOIN account_natureza an on (aa.natureza_conta_id = an.id)
    LEFT JOIN res_currency c on (l.currency_id=c.id)
    LEFT JOIN account_move_reconcile partialrec
        on (l.reconcile_partial_id = partialrec.id)
    LEFT JOIN account_move_reconcile fullrec on (l.reconcile_id = fullrec.id)
    LEFT JOIN res_partner p on (l.partner_id=p.id)
    LEFT JOIN account_invoice i on (m.id =i.move_id)
    LEFT JOIN account_period per on (per.id=l.period_id)
    JOIN account_journal j on (l.journal_id=j.id)
    WHERE l.id in %s"""
    monster += (" ORDER BY %s" % (order,))
    try:
        self.cursor.execute(monster, (tuple(move_line_ids),))
        res = self.cursor.dictfetchall()
    except Exception:
        self.cursor.rollback()
        raise
    return res or []


def _compute_init_balance(self, account_id=None, period_ids=None,
                          mode='computed', default_values=False):
    if not isinstance(period_ids, list):
        period_ids = [period_ids]
    res = {}

    if not default_values:
        if not account_id or not period_ids:
            raise Exception('Missing account or period_ids')
        try:

            self.cursor.execute(
                "SELECT an.name "
                "FROM account_account aa "
                "LEFT JOIN  account_natureza an "
                "   ON (aa.natureza_conta_id = an.id) "
                "WHERE aa.id = {}".format(account_id))

            natureza = self.cursor.dictfetchone().get('name')

            BALANCE = 'sum(debit)-sum(credit)'

            if natureza and natureza == 'Credora':
                BALANCE = 'sum(credit)-sum(debit)'

            self.cursor.execute(
                "SELECT sum(debit) AS debit, "
                " sum(credit) AS credit, "
                " {} AS balance, "
                " sum(amount_currency) AS curr_balance"
                " FROM account_move_line"
                " WHERE period_id in {}"
                " AND account_id = {}".format(
                    BALANCE, tuple(period_ids), account_id
                )
            )
            res = self.cursor.dictfetchone()
            res.update(natureza_conta=natureza)

        except Exception:
            self.cursor.rollback()
            raise

    return {'debit': res.get('debit') or 0.0,
            'credit': res.get('credit') or 0.0,
            'init_balance': res.get('balance') or 0.0,
            'init_balance_currency': res.get('curr_balance') or 0.0,
            'state': mode, 
            'natureza_conta': res.get('natureza_conta', ''),
            }


CommonReportHeaderWebkit._compute_init_balance = _compute_init_balance
CommonReportHeaderWebkit._get_move_line_datas = _get_move_line_datas
