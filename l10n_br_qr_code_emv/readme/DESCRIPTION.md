The Pix BR Code is the Brazilian profile of the EMV merchant-presented QR standard.
`account_qr_code_emv` already builds that payload: TLV serialization, CRC16 and the
common tags. What it cannot know is the country part, tag 26, which for Pix carries the
`br.gov.bcb.pix` GUI and the addressing key.

This module fills that gap, so a customer invoice can be paid by scanning the QR code with
any Brazilian bank app.

The addressing key is not duplicated here: it is read from `res.partner.pix`, which
`l10n_br_base` already validates for the four key types the Central Bank defines.
