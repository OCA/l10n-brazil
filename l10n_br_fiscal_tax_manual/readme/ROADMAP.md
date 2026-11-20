- A manual value of exactly 0 (zero) is treated as "not set", since 0 is
  falsy in Python/Odoo. It is currently not possible to force a tax value
  to zero through the manual value field; use the manual base field with a
  rate-based tax instead.
