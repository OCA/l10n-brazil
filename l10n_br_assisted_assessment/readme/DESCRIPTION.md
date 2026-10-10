Core of the Brazilian IBS/CBS assisted assessment (_apuração assistida_) introduced by
article 46 of Complementary Law 214/2025 and regulated by Decree 12,955/2026 (CBS) and
CGIBS Resolution 6/2026 (IBS).

Under the new model the tax administration calculates the monthly balance from the
taxpayer's electronic fiscal documents and presents it for confirmation. The taxpayer
can no longer assess from scratch: the own assessment exists only as an adjustment of
the presented one, and confirming, adjusting or **staying silent** all constitute the
tax credit.

This module provides the tribute-agnostic part of that cycle:

- monthly assessment periods per company and tribute, with the regulatory deadlines
  (presentation by the 15th, or the 20th when the taxpayer is required to file the DeRE,
  and confirmation by the last business day of the following month);
- the asynchronous request lifecycle, including the daily call quota imposed by the
  gateway;
- reconciliation of the presented lines against the booked fiscal documents, classifying
  every difference and suggesting how to repair it;
- deadline warnings and automatic expiration, so that silence is never silent.

The HTTP transport is not part of this module. The CBS is served by the Receita Federal
and the IBS by the CGIBS, each with its own endpoints, so transmission and payload
parsing are provided by separate transport addons that implement the `_transmit` and
`_parse_payload` hooks.
