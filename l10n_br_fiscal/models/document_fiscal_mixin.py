# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..constants.fiscal import (
    FISCAL_IN_OUT,
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT
)


class FiscalDocumentMixin(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.mixin'
    _description = 'Document Fiscal Mixin'

    def _date_server_format(self):
        return fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _default_operation(self):
        return False

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved'),
                  '|', ('company_id', '=', self.env.user.company_id.id),
                  ('company_id', '=', False)]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operation',
        domain=lambda self: self._operation_domain(),
        default=_default_operation)

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related='fiscal_operation_id.operation_type',
        string='Operation Type',
        readonly=True)

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string='Buyer Presence',
        default=NFE_IND_PRES_DEFAULT)

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='l10n_br_fiscal_document_mixin_comment_rel',
        column1='document_mixin_id',
        column2='comment_id',
        string='Comments',
    )

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False):

        model_view = super(FiscalDocumentMixin, self).fields_view_get(
            view_id, view_type, toolbar, submenu
        )
        return model_view  # TO REMOVE

        # if view_type == "form":
        #     fiscal_view = self.env.ref("l10n_br_fiscal.document_fiscal_mixin_form")
        #
        #     doc = etree.fromstring(model_view.get("arch"))
        #
        #     for fiscal_node in doc.xpath("//group[@name='l10n_br_fiscal']"):
        #         sub_view_node = etree.fromstring(fiscal_view["arch"])
        #
        #         from odoo.osv.orm import setup_modifiers
        #         setup_modifiers(fiscal_node)
        #         try:
        #             fiscal_node.getparent().replace(fiscal_node, sub_view_node)
        #             model_view["arch"] = etree.tostring(doc, encoding="unicode")
        #         except ValueError:
        #             return model_view
        #
        # return model_view

    @api.multi
    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # this will force to create a new fiscal document line:
        vals['fiscal_document_id'] = False

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals
