Transport for the CBS side of the assisted assessment, consuming the asynchronous APIs
published by the Receita Federal in September 2026.

It implements the hooks left open by `l10n_br_assisted_assessment`:

- opens the debit and credit requests at `apuracao-cbs/v2`, using the 8 digit CNPJ root,
  since the assessment is consolidated per taxpayer and not per establishment;
- exposes the callback endpoint informed as `urlRetorno`, answering the `HEAD`
  validation the gateway performs before accepting a request and storing the pre-signed
  download URL that arrives afterwards;
- polls the status endpoint as a recovery path, because the callback is not always
  delivered;
- downloads and parses the returned file, dispatching its contents to the right
  assessment period. A single answer carries the current period along with adjustments
  to previous ones, and only what changed since the previous query, so the lines are
  merged instead of replaced.

The IBS is served by the CGIBS with its own endpoints and is therefore out of scope for
this addon.
