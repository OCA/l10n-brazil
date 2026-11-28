One connection per bank account, shared by every module that talks to the bank
through [brbank](https://pypi.org/project/brbank/): billing (boletos and Pix),
DDA (authorized direct debits) and whatever comes next. The credentials, the
access token, the OAuth consent and the webhook are configured once here
instead of once per domain.

- **Token shared between workers**: the access token lives in a table and its
  renewal runs under a lock of the database. Banks that rotate the refresh
  token (BTG) invalidate the old one at each renewal, so two processes renewing
  at the same time would lose it; here the second one reads the token the first
  one saved.
- **OAuth consent** (authorization code with PKCE) for the adapters that need
  it, started by the *Connect* button.
- **One webhook URL per connection**; the domain modules extend a hook to say
  what the notification means. An event nobody knows is not an error.
- **State of the connection** (not connected, connected, error, needs
  reconsent) and the **last synchronization of each domain**, shown on a kanban.
- Credentials readable only by system administrators.
