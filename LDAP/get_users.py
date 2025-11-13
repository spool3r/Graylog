import json
import configparser
import ssl
from ldap3 import Server, Connection, ALL, SIMPLE, Tls
from datetime import datetime

def query_active_directory():
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')

        AD_SERVER = config.get('ad_credentials', 'server')
        AD_USER = config.get('ad_credentials', 'user')
        AD_PASSWORD = config.get('ad_credentials', 'password')
        SEARCH_BASE = config.get('ad_credentials', 'search_base')
        CA_CERT_FILE = config.get('ad_credentials', 'ca_cert_file')
    except Exception as e:
        print(f"Error reading config.ini file: {e}")
        return None

    domain_parts = [part.split('=')[1] for part in SEARCH_BASE.split(',') if 'DC=' in part]
    domain_name = '.'.join(domain_parts)
    BIND_USER = f"{AD_USER}@{domain_name}"
    
    # Uncomment for Secure LDAP connection. Make sure to get Certificate for your AD and either rename it to ca_cert.cer or change the file name in the config.ini
    tls_config = Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=CA_CERT_FILE)
    server = Server(AD_SERVER, get_info=ALL, use_ssl=True, tls=tls_config)
    
    # Uncomment if you want to use a not secure connection to your LDAP. If using a this method, create a blank file called ca_cert.cer
    # server = Server(AD_SERVER, get_info=ALL, use_ssl=False)
    
    try:
        # Note: SIMPLE authentication over non-SSL sends credentials in plaintext.
        conn = Connection(server, user=BIND_USER, password=AD_PASSWORD, authentication=SIMPLE, auto_bind=True)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

    attributes_to_get = [
        'cn', 'givenName', 'sn', 'sAMAccountName', 'description',
        'employeeID', 'mail', 'whenCreated', 'pwdLastSet', 'whenChanged',
        'accountExpires', 'lastLogon', 'lastLogoff', 'lockoutTime', 'memberOf',
        'userAccountControl'
    ]

    all_users = []
    
    entry_generator = conn.extend.standard.paged_search(
        search_base=SEARCH_BASE,
        search_filter='(objectCategory=person)',
        search_scope='SUBTREE',
        attributes=attributes_to_get,
        paged_size=500,
        generator=True
    )

    for entry in entry_generator:
        if entry['type'] != 'searchResEntry':
            continue

        user_data = {}
        raw_attrs = entry['attributes']

        # --- CORRECTED ATTRIBUTE PROCESSING LOOP ---
        for attr in attributes_to_get:
            value = raw_attrs.get(attr)

            # This check now handles both missing attributes (None) and empty lists ([])
            if not value:
                user_data[attr] = None
                continue

            # Handle multi-valued attributes (like memberOf)
            if isinstance(value, list) and len(value) > 1:
                user_data[attr] = [str(item) for item in value]
            else:
                # Handle single values, which could be in a list or be a direct object
                item = value[0] if isinstance(value, list) else value
                
                # Properly format datetime objects for JSON
                if isinstance(item, datetime):
                    user_data[attr] = item.isoformat()
                else:
                    user_data[attr] = str(item)

        uac_value = raw_attrs.get('userAccountControl', 0)
        if isinstance(uac_value, list):
            uac_value = uac_value[0] if uac_value else 0

        is_disabled = bool(int(uac_value) & 2)
        user_data['disabled_account'] = is_disabled
        
        if 'userAccountControl' in user_data:
            del user_data['userAccountControl']

        all_users.append(user_data)

    conn.unbind()
    return all_users

if __name__ == "__main__":
    users = query_active_directory()
    if users:

        config = configparser.ConfigParser()
        config.read('config.ini')
        output_filename = config.get('output_files', 'users_json')
        output_json_in_csv_filename = config.get('output_files', 'users_json_in_csv')
        csv_key_column = config.get('output_files', 'csv_key_column')

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        print(f"✅ Successfully exported {len(users)} user accounts to '{output_filename}'")

        print(f"Saving user data as JSON inside of CSV file '{output_json_in_csv_filename}'")
        import csv
        with open(output_json_in_csv_filename, 'w') as csvfile:
            csvwriter = csv.writer(csvfile
                                    , delimiter='#'
                                    , quotechar='\''
                                    , quoting=csv.QUOTE_MINIMAL
                                    )
            csvwriter.writerow([csv_key_column, 'json_ad_user'])

            i = 0
            max = 100000
            for userobj in users:
                i = i + 1

                if i > max:
                    break
                
                if csv_key_column in userobj:
                    if "memberOf" in userobj and userobj["memberOf"]:
                        l_member_of = []
                        if isinstance(userobj["memberOf"], list):
                            # l_member_of = userobj["memberOf"]
                            for listitem in userobj["memberOf"]:
                                l_member_of.append(listitem.replace("\\", ""))
                        else:
                            l_member_of.append(userobj["memberOf"].replace("\\", ""))
                        
                        if len(l_member_of) == 1:
                            userobj["memberOf"] = l_member_of[0]
                        elif len(l_member_of) == 0:
                            userobj["memberOf"] = ""
                        else:
                            userobj["memberOf"] = l_member_of
                        
                    json_vals = json.dumps(userobj)

                    csvwriter.writerow([userobj[csv_key_column], json_vals])

        if i > 0:
            print(f"✅ Successfully exported {i} user accounts as JSON inside of CSV file '{output_json_in_csv_filename}'")
            print("".join([
                "CSV Config: "
                , "\n", "    ", "Separator: #"
                , "\n", "    ", "Quote character: '"
                , "\n", "    ", "Key column: sAMAccountName"
                , "\n", "    ", "Value column: json_ad_user"
            ]))
        else:
            print(f"Failed to export any users to '{output_json_in_csv_filename}'")

    else:
        print("❌ No users were exported. Please check the logs for errors.")