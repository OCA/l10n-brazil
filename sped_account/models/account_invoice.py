# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _map_move_template_domain(self, move_line, line_type, amt):
        """
        Método para mapear qual é o roteiro correto para cada tipo de
        lançamento ou manter as contas originais caso não exista roteiro que
        se encaixe na operação
        :param move_line:
        :param line_type:
        :return:
        """
        values_dict = {}
        values_dict = {'type': line_type}
        domain = ['&']
        invl = self.env['account.invoice.line'].browse(move_line.get('invl_id',
                                                                     False))
        duration = fields.Datetime.from_string(self.date_due) + relativedelta(
            years=-1)

        if duration > datetime.today():
            term = 'longo'
        else:
            term = 'curto'
        if invl:
            product = invl.product_id
            if product.type:
                values_dict.update(dict(
                    product_fiscal_type=product.fiscal_type,
                ))
            if product.origin:
                values_dict.update(dict(
                    product_origin=product.origin
                ))

        if line_type == 'tax':
            if move_line.get('account_id', False):
                values_dict.update(dict(
                    credit_account_id=move_line.get('account_id', False)
                ))

        if amt.id:
            values_dict.update(dict(
                template_id=amt.id,
            ))
        if term:
            values_dict.update(dict(
                term=term,
            ))

        for key, value in values_dict.iteritems():
            if key != 'template_id':
                domain.append('|')
            domain.append((key, '=', value))
            if key != 'template_id':
                domain.append((key, '=', False))

        return domain

    def define_account(self, move_line, line_type):
        """
        Definir contas das novas partidas de acordo com o roteiro contabil
        :param move_line:  - dict - partida duplicada para contra-partida
                                    na conta contabil
        :param line_type: sting - Tipo de partida
                                    ['CLIENTE', 'RECEITA', 'IMPOSTO']
        :return:
        """

        account_id = False
        amt = self.env['account.move.template'].search([(
            'fiscal_category_ids', '=', self.fiscal_category_id.id)])
        domain = self._map_move_template_domain(move_line, line_type, amt)
        amlt = self.env['account.move.line.template'].search(domain,
                                                             order='sequence',
                                                             limit=1)
        if line_type == 'tax':
            if move_line.get('credit', False):
                account_id = amlt.credit_account_id

            if move_line[2].debit:
                account_id = amlt.debit_account_id

        elif line_type == 'cost':
            invl = self.env['account.invoice.line'].browse(move_line.
                                                           get('invl_id',
                                                               False))
            prod = invl.product_id
            value = prod.standard_price
            if amt.purchase_installed:
                print 'purchase installed'
                print value
                if prod.cost_method == 'real':
                    sm = self.env['stock.move'].search([(
                        'product_id', '=', prod.id)], limit=1, order='id')
                    if sm.price_unit:
                        value = sm.price_unit

                elif prod.cost_method == 'average':
                    tmpl_dict = {}
                    for move in self.env['stock.move'].search([(
                            'product_id', '=', prod.id)]):
                        # adapt standard price on incomming moves if
                        # the product cost_method is 'average'
                        # if (move.location_id.usage == 'supplier'):
                        product = move.product_id
                        prod_tmpl_id = move.product_id.product_tmpl_id.id
                        qty_available = move.product_id.product_tmpl_id.\
                            qty_available
                        if tmpl_dict.get(prod_tmpl_id):
                            product_avail = qty_available + tmpl_dict[
                                prod_tmpl_id]
                        else:
                            tmpl_dict[prod_tmpl_id] = 0
                            product_avail = qty_available
                        if product_avail <= 0:
                            new_std_price = move.price_unit
                        else:
                            # Get the standard price
                            amount_unit = product.standard_price
                            new_std_price = ((amount_unit * product_avail) +
                                             (move.price_unit * move.
                                              product_qty)) / (product_avail +
                                                               move.
                                                               product_qty)
                        tmpl_dict[prod_tmpl_id] += move.product_qty
                        value = new_std_price

            if move_line.get('credit', False):
                move_line['credit'] = value
                account_id = amlt.credit_account_id
            if move_line.get('debit', False):
                account_id = amlt.debit_account_id
                move_line['debit'] = value

        elif line_type == 'receipt':
            account_id = amlt.credit_account_id
        else:
            account_id = amlt.debit_account_id
        # elif line_type == 'tax':
        #     if move_line.get('debit', False):
        #         account_id = amlt.debit_account_id
        #     else:

        # Se definir uma conta no mapeamento, seta a conta,
        # senão fica com a conta padrão
        if account_id:
            move_line['account_id'] = account_id.id
            print 'Conta encontrada'
            print account_id

        if line_type == 'receipt' and amt.use_cost:
            return True
        return False

    def finalize_invoice_move_lines(self, move_lines):
        """
        Sobrescrever hook do core para criar as contrapartidas de acordo com
        o tipo da partida e mapear as contas seguindo o roteiro contábil.
        :param move_lines: lista com [0,0, dict] - Move lines geradas pelo core
        :return: - lista com [0,0, dict] onde o dict são as partidas a serem
                                        criadas para o lançamento contabil
                                        da invoice.
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        lines = list(move_lines)
        for move in lines:
            move_line = move[2]
            if move_line.get('product_id', False):
                line_type = 'receipt'
                invl = self.env['account.invoice.line'].browse(
                    move_line.get('invl_id', False))
                # Adiciona o valor dos impostos no lançamento de receita para
                # gerar a receita bruta
                move_line['credit'] += invl.ipi_value
                move_line['credit'] += invl.icms_value
                move_line['credit'] += invl.pis_value
                move_line['credit'] += invl.cofins_value
                move_line['credit'] += invl.ir_value
                move_line['credit'] += invl.issqn_value
                move_line['credit'] += invl.csll_value
                move_line['credit'] += invl.inss_value
                move_line['credit'] += invl.ii_value
                move_line['credit'] += invl.icms_fcp_value
                move_line['credit'] += invl.icms_dest_value
                move_line['credit'] += invl.icms_st_value

            elif move_line.get('tax_amount', False):
                line_type = 'tax'

            else:
                line_type = 'client'

            # Criar contra-partidas
            if line_type == 'tax':
                partida = dict(move_line)
                partida['debit'] = move_line['credit']
                partida['credit'] = move_line['debit']
                self.define_account(partida, line_type)
                move_lines.append([0, 0, partida])

            cost = self.define_account(move_line, line_type)
            if cost:
                custo = dict(move_line)
                self.define_account(custo, 'cost')
                # calcular custo
                estoque = dict(custo)
                estoque['debit'] = custo['credit']
                estoque['credit'] = custo['debit']
                self.define_account(estoque, 'cost')
                move_lines.append([0, 0, custo])
                move_lines.append([0, 0, estoque])

        return move_lines

    def line_get_convert(self, line, part, date):
        res = super(AccountInvoice, self).line_get_convert(line, part, date)
        res.update(dict(
            invl_id=line.get('invl_id', False)
        ))
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        res.update(dict(
            invl_id=line.id
        ))
        return res
