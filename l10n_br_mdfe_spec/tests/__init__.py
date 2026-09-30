# The test builds new (in memory) records of the abstract spec models, it does
# not turn them into concrete models anymore. Disable it again if it ever
# conflicts with l10n_br_mdfe once that module is migrated.
from . import test_mdfe_import
