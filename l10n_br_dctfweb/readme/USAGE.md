Go to Invoicing > Accounting > Actions > DCTFWeb/MIT and create the assessment
of the month.

**Assess.** The button reads every persisted tax assessment of the month whose
tax group has a revenue code, and writes one debit per assessment. The
confessed amount is the assessed balance, field 11 of the E110, not the amount
payable: a withholding does not shrink the confession, it is matched against
the debit inside the DCTFWeb. Assessing again rebuilds the debits that came
from the books and keeps the manual ones.

**Complete.** Add by hand what the books do not model: a debit of a tax the
tax assessment does not cover, a special event of the month, a lawsuit that
suspends part of a debit.

**Close.** The button refuses to close while there is a pendency, and lists
all of them at once: a missing establishment on an IPI debit, a responsible
without a CPF, a suspension without its court. Closing freezes the JSON file
on the assessment.

**Export.** The file is named after the CNPJ root of the company, the period
and the layout suffix, so it can be imported in the e-CAC as it is.

**Without movement.** Tick it when there was no taxable fact in the month.
File it once: the DCTFWeb no longer asks for the yearly renewal of inactivity,
and an omitted assessment without movement costs the minimum fine.

**Rectify.** A transmitted assessment is not edited: the Rectify button opens a
new one for the same period, numbered in sequence, keeping the transmitted one
as it was.
