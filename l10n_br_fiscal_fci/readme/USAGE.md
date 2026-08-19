Go to *Fiscal > Product and Service > FCI* and create a new FCI.

1. Select the company whose establishment is declaring the FCI and add one
   line per goods, filling in the *Interstate Output Amount* and the
   *Imported Amount* per unit of measure. The *Import Content* is computed
   with the rounding rule of the manual (`ROUND(x;y)`).
2. Press **Generate File**. The TXT file is attached to the record with the
   name pattern `CNPJ_AAAAMMDD_hhmmss.txt` required by the layout.
3. Download the file and validate/transmit it with the SEFAZ
   *Validador/Transmissor* application. Write the reception protocol
   returned by the TED in the *Reception Protocol* field and press
   **Confirm Transmission**.
4. One or two hours after the transmission, download the return file in the
   restricted query of the FCI web system ("Download Arquivo de Retorno"),
   press **Import Return File** and select the downloaded file (the TXT or
   the ZIP). The FCI control numbers are written in the goods lines and the
   FCI is set to done.

The FCI control number of the last FCI of a product is shown in the *Fiscal*
tab of the product form and the whole history is available in
*Fiscal > Product and Service > FCI Goods*.
