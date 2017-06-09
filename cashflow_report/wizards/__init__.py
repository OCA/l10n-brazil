from . import financial_cashflow_wizard

# select aa.code, aa.name, date_trunc('month', fm.date_maturity) as Month, sum(fm.amount_total * fm.sign)  from financial_move fm join account_account_tree_analysis aat on aat.child_account_id =  fm.account_id join account_account aa on aa.id = aat.parent_account_id  where fm.type in ('2receive', '2pay') and fm.date_maturity >= '2017-01-01' and fm.date_maturity <= '2017-12-01'  group by aa.code, aa.name, Month
