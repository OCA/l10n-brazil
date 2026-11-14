After installation:

1. Navigate to **Settings > Technical > Parameters > System Parameters**.
2. The FTP URL defaults to the MTE public server. If you need to override it,
   set the key ``l10n_br_hr_employee_ppe.caepi_ftp_url`` to the desired URL.
3. Go to **Settings > Technical > Scheduled Actions** and activate
   **CAEPI: Refresh CA Database (MTE)**. The default interval is daily.
4. Run the action manually once to populate the local database.
