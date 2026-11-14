This module adds automatic lookup of PPE Certificates of Approval (CA)
from the Brazilian Ministry of Labor (MTE) public database.

The MTE publishes a daily export of every CA ever issued
(approximately 42 000 unique certificates). A scheduled action downloads
this file, parses and deduplicates it, and upserts the results into a
local ``caepi.certificate`` table.

When a PPE product's CA number is filled in, the system automatically
populates the certificate expiry date, equipment description, manufacturer
and current MTE status (Valid / Expired / Suspended / Cancelled).
