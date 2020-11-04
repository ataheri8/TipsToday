
E = {
    'clients_name_exists': 'client_name_exists',
    'clients_unable_to_create': 'client_unable_to_create',
    'clients_program_not_found': 'clients_program_not_found',
    'clients_id_not_found': 'client_not_found',
    'clients_unable_to_deactivate': 'client_unable_to_deactivate',
    'clients_field_empty': 'no_clients_exist',
    'clients_program_not_found': 'client_program_id_not_found',
    'clients_unable_to_set_flags': 'client_unable_to_set_flags',
    'clients_flags_not_found': 'client_no_flags_set',

    'wallets_unable_to_create': 'wallets_unable_to_add_wallet',
    'wallets_unable_to_deactivate': 'wallets_unable_to_deactivate',
    'wallets_id_not_found': 'wallet_not_found',
    'wallets_client_wallet_mismatch': 'wallet_does_not_belong_to_client',
    'wallets_cannot_update_amount': 'wallet_cannot_fund',
    'wallets_cannot_audit_adjustment': 'wallet_cannot_audit_adjustment',
    'wallets_unable_to_decrement': 'wallet_unable_to_decrement',

    'customer_unable_to_create': 'customer_unable_to_create',
    'customer_not_found': 'employee_id_invalid',
    'customer_client_id_invalid': 'invalid_client_id_match',
    'proxy_key_not_found': 'invalid_proxy_key',
    'customer_person_id_invalid': 'invalid_person_id',

    'super_admins_identifier_exists': 'super_admin_identifier_exists',
    'super_admins_unable_to_create': 'super_admin_unable_to_create',
    'super_admins_id_not_found': 'super_admin_not_found',
    'super_admins_unable_to_disable': 'super_admin_cannot_disable',
    'super_admins_unable_to_enable': 'super_admin_cannot_enable',
    'super_admins_identifier_not_found': 'super_admin_invalid_credentials',
    'super_admins_invalid_credentials': 'super_admin_invalid_credentials',
    'super_admins_not_active': 'super_admin_not_active',
    'super_admins_invalid_authorization': 'super_admin_session_not_active',
    'super_admins_unable_to_clear_session': 'super_admin_no_logout',

    'admins_identifier_exists': 'admin_identifier_exists',
    'admins_unable_to_create': 'admin_unable_to_create',
    'admins_id_not_found': 'admin_not_found',
    'admins_unable_to_disable': 'admin_cannot_disable',
    'admins_unable_to_enable': 'admin_cannot_enable',
    'admins_invalid_client_id': 'admin_invalid_client_id',
    'admins_invalid_wallet_id': 'admin_invalid_wallet_id',
    'admins_client_id_wallet_id_mismatch': 'admin_invalid_client_data',
    'admins_mismatched_client_id': 'admin_invalid_client_data',
    'admins_identifier_not_found': 'admin_invalid_credentials',
    'admins_invalid_credentials': 'admin_invalid_credentials',
    'admins_not_active': 'admin_not_acive',
    'admins_invalid_authorization': 'admin_session_not_active',
    'admins_unable_to_clear_session': 'admin_no_logout',
    'admins_unable_to_start_payout': 'admin_unable_to_start_payout',
    'admins_unable_to_adjust_amount_processor': 'admin_unable_adjust_amount_at_processor',
    'admins_unable_to_complete_payout': 'admin_unable_to_complete_payout',
    'admins_invalid_customer_access': 'admin_invalid_customer_access',

    'customers_identifier_exists': 'customer_identifier_exists',
    'customers_id_not_found': 'customer_not_found',
    'customers_invalid_client_id': 'customer_invalid_client_id',
    'customers_unable_to_create': 'customer_unable_to_create',
    'customers_identifier_not_found': 'customer_invalid_credentials',
    'customers_invalid_credentials': 'customer_invalid_credentials',
    'customers_not_active': 'customer_not_active',
    'customers_no_security_update': 'customer_update_pass_fail',
    'customers_unable_to_write_security_reset': 'customers_system_error',
    'customers_invalid_reset_token': 'customer_invalid_reset_token',
    'customers_invalid_person_id': 'customer_invalid_person_id',
    'customers_invalid_store_id': 'customer_invalid_store_id',
    'customers_cannot_update_proxy_status': 'customer_cannot_update_proxy_status',
    'customers_unable_add_address': 'customer_unable_to_add_address',
    'customers_address_not_found': 'customer_address_not_found',
    'customers_proxy_client_mismatch': 'customer_proxy_client_mismatch',
    'customers_proxy_not_found': 'customer_proxy_not_found',
    'customers_proxy_not_available': 'customer_proxy_not_available',
    'customers_has_active_card': 'customer_has_active_card',
    'customers_unable_to_create_proxy_db': 'customer_unable_to_save_proxy',
    'customers_unable_to_mark_proxy_assigned': 'customer_cannot_mark_assigned',
    'customers_no_proxies': 'customer_no_proxies',
    'customers_invalid_proxy_for_customer': 'customer_invalid_proxy',
    'customers_address_missing': 'customer_missing_required_address',
    'customers_unable_to_activate_with_processor': 'customer_unable_to_activate_with_processor',
    'customers_no_active_proxy': 'customer_no_active_proxy',
    'customers_unable_to_retrieve_balance': 'customer_cannot_load_balance',
    'customers_unable_retrieve_txns': 'customer_cannot_get_txns',
    'customers_unable_to_retrieve_proxy_status': 'customer_cannot_load_proxy_status',
    'customers_employee_id_exists': 'customer_employee_id_exists',
    'customers_unable_to_initiate_pass_reset': 'customer_unable_to_initiate_pass_reset',
    'customers_phone_number_invalid': 'customer_phone_number_invalid',
    'customers_phone_validation_exception': 'customer_cannot_validate_phone_number',

    'invalid_status_code': 'invalid_status_code',

    'sessions_invalid_session': 'session_not_valid',
    'sessions_unable_to_clear_session': 'session_no_clear',

    'stores_exists_for_client': 'store_exists_for_client',
    'stores_invalid_client_id': 'store_invalid_client_id',
    'stores_invalid_wallet_id': 'store_invalid_wallet_id',
    'stores_unable_to_create': 'store_unable_to_create',
    'stores_unable_to_disable': 'store_unable_to_disable',
    'stores_unable_to_enable': 'store_unable_to_enable',
    'stores_id_not_found': 'store_id_not_found',
    'stores_no_active_wallet': 'store_has_no_active_wallet',
    'stores_insufficient_wallet_balance': 'store_insufficient_wallet_balance',
    'stores_address_not_found': 'store_no_address_found',
    'stores_bank_account_exists': 'store_bank_account_exists',
    'stores_bank_account_add_failure': 'store_unable_to_add_bank_account',
    'stores_bank_account_not_found': 'store_bank_account_not_found',
    'stores_bank_account_cannot_update': 'store_bank_account_cannot_update',

    'fees_unable_to_disable': 'fee_unable_to_disable',
    'fees_unable_to_enable': 'fee_unable_to_enable',
    'fees_invalid_client_id': 'fee_invalid_client_id',
    'fees_unable_to_create': 'fee_unable_to_create',
    'fees_exists_for_event_type': 'fee_exists_for_event_type',

    'programs_unable_to_create': 'program_cannot_create',
    'programs_unable_to_view': 'program_cannot_view',
    'programs_unable_to_disable': 'program_unable_to_disable',
    'programs_unable_to_enable': 'program_unable_to_enable',
    'programs_id_not_found': 'program_id_not_found',

    'etransfers_recipient_exists': 'etransfer_recipient_exists_for_customer',
    'etransfers_cannot_create_recipient': 'etransfer_cannot_create_recipient',
    'etransfers_recipient_not_found': 'etransfer_record_not_found_for_customer',
    'etransfers_cannot_create_remote_contact': 'etransfer_cannot_create_contact',
    'etransfers_security_answer_wrong_size': 'etransfer_security_answer_wrong_size',
    'etransfers_invalid_recipient_id': 'etransfer_invalid_recipient_id',
    'etransfers_cannot_update_recipient': 'etransfer_cannot_update_recipient',
    'etransfers_cannot_create_remote_contact': 'etransfer_cannot_update_remote_recipient',
    'etransfers_unable_to_deactivate': 'etransfer_unable_to_deactivate',
    'etransfers_unable_to_check_proxy': 'etransfer_cannot_check_proxy',
    'etransfers_insufficent_funds': 'etransfer_insufficent_funds',
    'etransfers_cannot_debit_amount': 'etransfer_cannot_debit_amount',
    'etransfers_unable_to_create_etransfer': 'etransfer_unable_to_create_etransfer',

    'bill_payments_search_token_too_small': 'bill_payment_search_token_too_small',
    'bill_payments_no_remote_search': 'bill_payment_no_remote_search',
    'bill_payments_payee_exists': 'bill_payee_record_exists',
    'bill_payments_cannot_create_payee': 'bill_payee_cannot_create_record',
    'bill_payments_payee_no_exist_customer': 'bill_payee_not_with_user',
    'bill_payments_payee_not_found': 'bill_payee_not_found',
    'bill_payemns_cannot_disable_payee': 'bill_payee_cannot_disable',
    'bill_payments_cannot_update_payee': 'bill_payee_cannot_update',
    'bill_payments_unable_to_check_proxy': 'bill_payment_cannot_check_proxy',
    'bill_payments_insufficent_funds': 'bill_payment_insufficient_funds',
    'bill_payments_cannot_debit_amount': 'bill_payment_cannot_debit_amount',
    'bill_payments_unable_to_create_payment': 'bill_payment_unable_to_create_payemnt',

}

