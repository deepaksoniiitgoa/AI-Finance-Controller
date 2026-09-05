import pandas as pd
import random
import data_generator

fake = data_generator.fake
PAYMENT_METHODS = data_generator.PAYMENT_METHODS
SOURCES = data_generator.SOURCES
payment_method_mapping = {
    "UPI": "UPI_PAYMENT",
    "NET_BANKING": "NETBANKING",
    "CARD": "DEBIT_CARD",
    "WALLET": "E_WALLET"
}

# Injection Logs
INJECTION_LOG = []
def log_injection(transaction_id, source, issue, details=""):
    INJECTION_LOG.append({ "transaction_id": transaction_id, "source": source, "issue": issue, "details": details})

# Missing records per source
def drop_records(source, source_name, id_column , already_drpped):
    indices = random.sample(list(set(source.index) - set(already_drpped)), random.randint(3, 6))
    already_drpped.extend(indices)
    for idx in indices:
        log_injection(source.at[idx, id_column], source_name,"MISSING_RECORD")

    source = source.drop(indices)
    return source , already_drpped

# Amount mismatches
def amount_mismatch(source, source_name, id_column):
    indices = random.sample(list(source.index) , random.randint(5 , 8))
    for idx in indices :
        original_amount = source.loc[idx , "amount"]
        fee = random.randint( 5, 50)
        new_amount = round(original_amount - fee , 2)
        source.loc[idx , "amount"] = new_amount
        log_injection(source.at[idx, id_column], source_name,"AMOUNT_MISMATCH" , details=f"{source_name} fee = {fee}")

    return source

# Timestamp drift beyond a "safe" window
def timestamp_drift(source , source_name , id_column):
    indices = random.sample(list(source.index) , 5)
    for idx in indices:
        original_time = source.loc[idx , "timestamp"]
        time_difference = random.randint(1  , 2)  # in days
        new_time = original_time + pd.Timedelta(days=time_difference)
        source.loc[idx , "timestamp"] = new_time
        log_injection(source.at[idx, id_column], source_name,"TIMESTAMP_DRIFT" , details=f"Bank timestamp shifted by {time_difference} day(s)")

    return source

# Duplicate Entries
def add_duplicate_records(source , source_name , id_column):
    indices = random.sample(list(source.index), min(3, len(source)))
    duplicates = source.loc[indices].copy()
    for idx in indices:
        original_id = source.loc[idx , id_column]
        new_id = f"{original_id}_DUP"
        duplicates.loc[idx, id_column] = new_id
        log_injection(source.at[idx, id_column], source_name,"DUPLICATE_ENTRY" , details=f"Duplicate {source_name} id = {new_id}")
        
    source = pd.concat([source, duplicates], ignore_index=True)
    return source

# A few "orphan" records that don't exist in Ground Truth at all
def add_orphan_records(source, source_name , id_column):
    for i in range(3):
        if source_name == SOURCES[0] :
            txn_id = f"ORPHAN_PAY_{fake.uuid4()}"
        elif source_name == SOURCES[1] :
            txn_id = f"ORPHAN_LED_{fake.uuid4()}"
        else:
            txn_id = f"ORPHAN_UTR_{fake.uuid4()}"

        orphan = {
            "order_id": f"ORPHAN_ORD_{i+1}",
            "merchant_id": f"MER_{random.randint(1, 10):03d}",
            "customer_id": f"CUS_{random.randint(1, 100):04d}",
            "amount": round(random.uniform(100, 100000), 2),
            "currency": "INR",
            "payment_method": random.choice(PAYMENT_METHODS),
            "transaction_type": "PAYMENT",
            "timestamp": fake.date_time_between(
                start_date="-30d",
                end_date="now"
            ),
            id_column: txn_id,
            "status": "SUCCESS"
        }
        source = pd.concat([source, pd.DataFrame([orphan])],ignore_index=True)
        log_injection(txn_id, source_name,"ORPHAN_RECORD" , details="Transaction does not exist in Ground Truth")

    return source

# Field-level variation
def field_variation(source , source_name , id_column):
    indices = random.sample(list(source.index) , 4)
    for idx in indices :
        original_method = source.loc[idx , "payment_method"]
        if original_method in payment_method_mapping :
            new_method = payment_method_mapping[original_method]
            source.loc[idx , "payment_method"] = new_method
            log_injection(source.loc[idx , id_column] , source_name,"FIELD_VARIATION" , details=f"Original Method = {original_method} , New Method = {new_method}")

    return source
