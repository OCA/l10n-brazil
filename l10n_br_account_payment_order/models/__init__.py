from . import account_journal
from . import account_move
from . import l10n_br_cnab_change_methods
from . import account_move_line
from . import l10n_br_cnab_boleto_fields
from . import l10n_br_cnab_payment_fields
from . import account_payment_mode
from . import account_payment_order
from . import account_payment_line
from . import account_payment
from . import l10n_br_cnab_event
from . import l10n_br_cnab_lot
from . import l10n_br_cnab_return_log
from . import ir_attachment
from . import l10n_br_cnab_data_abstract

# TODO: Ao remover os objetos que ficaram obsoletos com a unificação dos Códigos
#  no l10n_br_cnab.code acontece o erro abaixo, isso deixa de acontecer em
#  versões posteriores a 16.0.2.0.0, porém para evitar problemas como o que ocorreu
#  na v14 será melhor aguardar mesmo que por 6 meses ou mesmo apenas na migração
#  para a v17 para remover esses objetos e assim evitar qualquer possibilidade
#  de problema com migrações
# ERROR db odoo.modules.registry: Failed to load registry
# Traceback (most recent call last):
#  File "/usr/local/lib/python3.10/site-packages/odoo/tools/convert.py",
#  line 698, in _tag_root
#    f(rec)
#  File "/usr/local/lib/python3.10/site-packages/odoo/tools/convert.py", line 515,
#  in _tag_record
#    record = env['ir.model.data']._load_xmlid(xid)
#  File "/usr/local/lib/python3.10/site-packages/odoo/addons/base/models/ir_model.py",
#  line 2162, in _load_xmlid
#    record = self.env.ref(xml_id, raise_if_not_found=False)
#  File "/usr/local/lib/python3.10/site-packages/odoo/api.py", line 600, in ref
#    record = self[res_model].browse(res_id)
#  File "/usr/local/lib/python3.10/site-packages/odoo/api.py", line 550, in __getitem__
#    return self.registry[model_name](self, (), ())
#  File "/usr/local/lib/python3.10/site-packages/odoo/modules/registry.py",
#  line 190, in __getitem__
#    return self.models[model_name]
# KeyError: 'l10n_br_cnab.mov.instruction.code'
from . import l10n_br_cnab_return_move_code
from . import l10n_br_cnab_mov_intruction_code
from . import l10n_br_cnab_boleto_wallet_code
from . import l10n_br_cnab_code
