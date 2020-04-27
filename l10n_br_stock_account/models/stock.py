# Copyright (C) 2020  Magno Costa - Akretion
# Copyright (C) 2016  Renato Lima - Akretion
# Copyright (C) 2016  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields


class StockRule(models.Model):
    _name = "stock.rule"
    _inherit = [
     _name,
     "stock.invoice.state.mixin",
     "l10n_br_fiscal.document.line.mixin"
    ]

    # TODO - The method don't work because in _get_stock_move_values
    #  at "if field in values:" the parameter values don't has the fields
    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['invoice_state', 'operation_id', 'operation_line_id']
        return fields

    def _get_stock_move_values(
        self, product_id, product_qty, product_uom, location_id, name, origin,
            values, group_id):
        """
        Returns a dictionary of values that will be used to create a stock
         move from a procurement. This function assumes that the given procurement
          has a rule (action == 'pull' or 'pull_push') set on it.

        :param procurement: browse record
        :rtype: dictionary
        """
        date_expected = fields.Datetime.to_string(
            fields.Datetime.from_string(
                values['date_planned']) - relativedelta(days=self.delay or 0)
        )
        # it is possible that we've already got some move done, so check for the
        # done qty and create
        # a new move with the correct qty
        qty_left = product_qty
        move_values = {
            'name': name[:2000],
            'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or values['company_id'].id,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.partner_address_id.id or (values.get('group_id', False) and values['group_id'].partner_id.id) or False,
            'location_id': self.location_src_id.id,
            'location_dest_id': location_id.id,
            'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
            'rule_id': self.id,
            'procure_method': self.procure_method,
            'origin': origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
            'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.propagate,
            'priority': values.get('priority', "1"),
            # TODO - Fields below should be in the method
            #  _get_custom_move_fields
            'invoice_state': self.invoice_state,
            'operation_id': self.operation_id.id,
            'operation_line_id': self.operation_line_id.id,
        }
        for field in self._get_custom_move_fields():
            # TODO - The fields don't appear in parameter
            #  values, check from where come this
            if field in values:
                move_values[field] = values.get(field)
        return move_values
