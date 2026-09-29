Open _Assisted Assessment > Assessments_ and create one record per tribute and period,
using the `YYYY-MM` format. The presentation date and the deadline are computed from the
period and the company configuration.

The monthly routine has three steps:

1. **Download** the assessment presented by the tax administration, with _Request
   Debits_ and _Request Credits_. Both buttons require a transport addon; without one,
   paste the payload into the request and apply it. Debits and credits are separate
   services, so a direction that has not been downloaded yet never produces divergences.
2. **Reconcile** against the bookkeeping. Every assessment line is matched by access key
   to an authorised fiscal document and classified as a different value, a document only
   in the assessment, a document only in the bookkeeping or a credit that was not
   granted. Each divergence carries the action that repairs it, since adjustments are
   made by issuing fiscal documents.
3. **Confirm** the assessment. Confirming requires every divergence to be handled or
   ignored, because it constitutes the tax credit and implies acknowledgement of debt.

A daily scheduled action warns the responsible users as the deadline approaches and
marks the period as expired once it passes. An expired period means the balance
presented by the tax administration was presumed correct and the tax credit was
constituted without any manifestation.
