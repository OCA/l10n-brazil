/** @odoo-module **/
/* Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
 * License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html */

import {Component} from "@odoo/owl";
import {FileUploader} from "@web/views/fields/file_handler";
import {ListController} from "@web/views/list/list_controller";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

/**
 * Upload button of the FCI list view. It sends the selected file to the
 * import wizard, which creates or updates the FCI it holds.
 */
export class FCIFileUploader extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    async onFileUploaded(file) {
        const action = await this.orm.call(
            "l10n_br_fiscal.fci.import.wizard",
            "action_import_file",
            [file.name, file.data],
            {context: this.env.searchModel.context}
        );
        await this.action.doAction(action, {
            onClose: () => this.env.searchModel._notify(),
        });
    }
}
FCIFileUploader.components = {FileUploader};
FCIFileUploader.template = "l10n_br_fiscal_fci.FCIFileUploader";

export class FCIListController extends ListController {}
FCIListController.components = {
    ...ListController.components,
    FCIFileUploader,
};

export const FCIListView = {
    ...listView,
    Controller: FCIListController,
    buttonTemplate: "l10n_br_fiscal_fci.ListView.Buttons",
};

registry.category("views").add("fci_tree", FCIListView);
