/** @odoo-module **/

import {DfeBanner} from "../../components/dfe_banner/dfe_banner.esm";
import {ListController} from "@web/views/list/list_controller";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

/**
 * List view that shows the DF-e distribution panel above the records.
 *
 * Until 16.0 the panel came from the ``banner_route`` list attribute, with the
 * web client calling that route and injecting the returned HTML. Odoo 18 no
 * longer renders it (``bannerRoute`` survives only as a declared view prop),
 * so the panel is a regular Owl component now.
 *
 * The fiscal type comes from the action context (``default_fiscal_type``), so
 * the same js_class serves NF-e, NFS-e, CT-e or any other DF-e service. With
 * no fiscal type in the context the list behaves like a plain one.
 */
export class DfeDocumentListController extends ListController {
    static template = "l10n_br_fiscal_dfe.DfeDocumentListView";
    static components = {
        ...ListController.components,
        DfeBanner,
    };

    get fiscalType() {
        return this.props.context.default_fiscal_type;
    }

    reloadRecords() {
        return this.model.load();
    }
}

registry.category("views").add("dfe_document_list", {
    ...listView,
    Controller: DfeDocumentListController,
});
