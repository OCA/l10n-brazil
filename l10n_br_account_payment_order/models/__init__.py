# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import res_company
from . import account_invoice
from . import account_move
from . import account_move_line
from . import account_payment_mode
from . import account_payment_order
from . import account_payment_line
from . import account_payment
from . import bank_payment_line
# TODO - Separação dos dados de importação para um objeto especifico
#  cnab.return.log armazenando o LOG do Arquivo de Retorno CNAB
#  de forma separada e permitindo a integração com a alteração feita no
#  modulo do BRCobranca onde se esta utilizando o modulo
#  account_base_move_import para fazer essa tarefa de wizard de importação,
#  o objeto l10n_br_cnab esta comentado para permitir, caso seja necessário,
#  a implementação de outra forma de importação pois tem os metodos que eram
#  usados pela KMEE e o historico git do arquivo
# from . import l10n_br_cnab
from . import l10n_br_cnab_evento
from . import l10n_br_cnab_lote
from . import cnab_return_move_code
from . import cnab_return_log
from . import ir_attachment
