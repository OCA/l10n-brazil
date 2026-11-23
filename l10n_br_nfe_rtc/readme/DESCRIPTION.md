Exports the IBS split produced by ``l10n_br_fiscal_rtc`` in the NF-e/NFC-e.

``l10n_br_nfe`` writes the whole IBS in ``gIBSUF`` and hardcodes ``gIBSMun``
to zero. That was acceptable during the 2026 test year, when the municipal IBS
rate is 0%, but from 2027 the IBS is 0.05% for the State and 0.05% for the
Municipality, and from 2029 each State and each Municipality sets its own
rate: the two groups must carry their own rate, reduction and value.

The override only applies to lines whose ``rtc_status`` is ``calculated``:
every other line keeps the historical export, so the module can be installed
without changing the documents of the transition period.
