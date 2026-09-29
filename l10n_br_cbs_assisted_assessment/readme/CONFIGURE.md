Go to _Settings > Companies_, open the company and use the **Assisted Assessment** tab,
group **CBS Transport**:

- **Environment**: restricted production (`apuracao-cbs-prr/v2`) or production
  (`apuracao-cbs/v2`).
- **Client Id** and **Client Secret**: Receita Integra credentials of the head office.
  They are requested per service, so they are not necessarily the same credentials used
  for the DeRE. The manual for generating them is published at
  <https://arquivos.receitafederal.gov.br> under _Documentos > Técnicos > Receita
  Integra_.
- **Callback URL**: generated on first use and shown for copying. It embeds a secret and
  is the URL informed as `urlRetorno`.

Two requirements come from the gateway and are not enforced by the addon:

- the callback URL must be reachable from the internet over **HTTPS** with a valid
  certificate. An instance behind a reverse proxy needs `web.base.url` set to the public
  address; a plain HTTP URL is only logged as a warning so that the homologation
  environment can be exercised from a development instance;
- the opening endpoint accepts **4 calls a day** per service, answering HTTP 429 beyond
  that. The addon counts the calls and refuses to exceed the quota.

Two scheduled actions are provided. _Poll and download pending requests_ runs every 15
minutes and is enabled; _Open the daily requests_ is disabled by default and opens the
debit and credit requests of the current period for every company holding credentials.

This Doodba development stack ships a fake gateway at `cbs-assessment-mock:18951`
(published on the host as `127.0.0.1:18951`). Point **Token URL** at
`http://cbs-assessment-mock:18951/token` and **API URL** at
`http://cbs-assessment-mock:18951`. Any client id and secret are accepted. The
returned file only contains October 2026. A callback URL containing `mock-refuse`
is answered with `APURACAO-001`.
