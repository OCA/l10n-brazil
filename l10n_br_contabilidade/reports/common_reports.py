# -*- coding: utf-8 -*-

from openerp.addons.account_financial_report_webkit.report.general_ledger \
    import CommonReportHeaderWebkit


def _get_move_line_datas(self, move_line_ids,
                         order='per.special DESC, l.date ASC, \
                             per.date_start ASC, m.name ASC'):

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
                WHEN LEFT(an.name, 1) = 'C' THEN
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


CommonReportHeaderWebkit._get_move_line_datas = _get_move_line_datas
