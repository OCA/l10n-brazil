from odoo import fields, models

# TODO Temporary fixes
# Check if it is possible to make the lib that generates the odoo mixins (nfelib)
# apply these changes.


class DetPag(models.AbstractModel):
    _inherit = "nfe.40.detpag"

    nfe40_indPag = fields.Selection(
        selection=[
            ("0", "Pagamento à Vista"),
            ("1", "Pagamento à Prazo"),
        ],
        string="Forma de Pagamento",
        help="Indicador da Forma de Pagamento",
    )
