# Example JSON in CSV File

```csv
sAMAccountName#json_ad_user
lockout#{"cn": "lock m. out", "givenName": "lock", "sn": "out", "sAMAccountName": "lockout", "description": null, "employeeID": null, "mail": null, "whenCreated": "2025-06-04T20:38:24+00:00", "pwdLastSet": "2025-06-04T20:38:24.482798+00:00", "whenChanged": "2025-06-04T20:38:24+00:00", "accountExpires": "9999-12-31T23:59:59.999999+00:00", "lastLogon": "1601-01-01T00:00:00+00:00", "lastLogoff": "1601-01-01T00:00:00+00:00", "lockoutTime": null, "memberOf": null, "disabled_account": false}
graylog#{"cn": "Gary H. Logss", "givenName": "Gary", "sn": "Logss", "sAMAccountName": "graylog", "description": "hello", "employeeID": null, "mail": null, "whenCreated": "2024-11-06T16:45:50+00:00", "pwdLastSet": "2025-04-10T16:40:59.959278+00:00", "whenChanged": "2025-05-27T14:58:23+00:00", "accountExpires": "9999-12-31T23:59:59.999999+00:00", "lastLogon": "2025-05-09T15:18:43.567583+00:00", "lastLogoff": "1601-01-01T00:00:00+00:00", "lockoutTime": null, "memberOf": null, "disabled_account": false}
```

Graylog CSV data adapter config:

Property | Value
---- | ----
Separator | `#`
Quote character | `'`
Key column | `sAMAccountName`
Value column | `json_ad_user`