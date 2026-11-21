Two things have to be configured before the first assessment.

**The revenue code of each tax group.** Go to Invoicing > Configuration >
Accounting > Tax Groups and set the MIT revenue code of every group whose
debits are confessed in the MIT. The code belongs to the group because the
group already carries the regime, and the code depends on the regime: a mixed
taxpayer, who already needs one group per regime, gets one code per regime.

A usual mapping for a company in general:

| Tax group        | Revenue code |
| ---------------- | ------------ |
| PIS cumulative      | 8109-02   |
| PIS non cumulative  | 6912-01   |
| COFINS cumulative      | 2172-01 |
| COFINS non cumulative  | 5856-01 |
| IPI                    | the code of the taxed product |

Leave the code empty for a group the MIT does not cover, ICMS being the
obvious one. An assessment whose group has no code is skipped, and the reason
is posted in the chatter: silence there would be a trap.

**The initial data of the company.** Go to Settings > Companies > your company
> DCTFWeb/MIT and fill in the qualification of the legal entity, the form of
profit taxation, the monetary variation criterion, the PIS/COFINS regime and
the responsible for the assessment. This data barely changes from one month to
the next, so a new assessment starts filled in and the accountant only touches
what actually changed.
