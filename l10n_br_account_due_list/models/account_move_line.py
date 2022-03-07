# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    """
    As linhas precisam ser criadas conforme sequencia de
    Data de Vencimentos/date_maturity senão ficam fora de ordem:
     ex.:
     N° da Parcela | Data de Vencimento
     001           |  06/03/2022
     002           |  05/05/2022
     003           |  05/04/2022
     Isso causa confusão pois como nesse exemplo a terceira parcela
     fica como sendo a segunda.

     Isso é importante também para a criação dos CNAB/Boletos:
     ex.: own_number 201 31/12/2020, own_number 202 18/11/2020
     Nesse caso a primeira parcela fica como sendo a segunda.
    """

    _inherit = "account.move.line"
    _order = "date desc, date_maturity ASC, id desc"
