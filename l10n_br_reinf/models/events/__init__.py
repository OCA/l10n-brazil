from . import reinf_r1000

# Read by spec_driven_model to resolve the schema and the version. The marker
# stays in this subpackage on purpose: the prefix is resolved from the module of
# the class, so marking the whole models package would make res_company.py
# answer "reinf21" too, and the registry would not load.
spec_schema = "reinf"
spec_version = "21"
