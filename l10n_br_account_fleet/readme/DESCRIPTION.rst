This module inserts the following snippet below into the form view of the invoice_line_ids field:

.. code-block:: xml

    <xpath
        expr="//field[@name='invoice_line_ids']/form/sheet/group/field[@name='account_id']"
        position="after"
    >
        <field name='need_vehicle' invisible='1' />
        <field
            name='vehicle_id'
            attrs="{'required': [('need_vehicle', '=', True), ('parent.move_type', 'in', ('in_invoice', 'in_refund'))], 'column_invisible': [('parent.move_type', 'not in', ('in_invoice', 'in_refund'))]}"
        />
    </xpath>

This implementation is necessary because, by default, invoice lines are added directly in the tree view. However, in the case of Brazilian localization, the inclusion of invoice lines is done through the form view. Therefore, the account_fleet module adds the necessary fields for integration between the accounting and fleet modules, specifically in the tree view of the invoice_line_ids field. Additionally, this module adds the same fields in the form view of the invoice lines. With this, the integration between accounting and the fleet module occurs seamlessly.
