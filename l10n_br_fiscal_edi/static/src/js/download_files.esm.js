/** @odoo-module **/

import {registry} from "@web/core/registry";
import {_t} from "@web/core/l10n/translation";

// A download of the browser carries one file. Asking for several unzipped means
// asking one at a time, with a breath between them: fired in the same tick the
// browser keeps only the last one.
const BREATH_MS = 300;

function ask(url) {
    const link = document.createElement("a");
    link.href = url;
    link.download = "";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function downloadFiles(env, action) {
    const {files = [], skipped = []} = action.params || {};
    for (const [position, file] of files.entries()) {
        if (position) {
            await wait(BREATH_MS);
        }
        ask(file.url);
    }
    if (skipped.length) {
        env.services.notification.add(skipped.join(", "), {
            title: _t("Without a file to download"),
            type: "warning",
        });
    }
}

registry.category("actions").add("l10n_br_fiscal_edi.download_files", downloadFiles);
