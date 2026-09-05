import pandas as pd
from faker import Faker
import random
from datetime import timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

N = 60
PAYMENT_METHODS = ["UPI" , "CARD" , "NET_BANKING" , "WALLET"]
TRANSACTION_TYPES = ["PAYMENT" , "REFUND" , "TRANSFER" , "WITHDRAWAL" , "DEPOSIT"]

# Generate Ground Truth
GROUND_TRUTH = []
for i in range(N):
    transaction_id = f"TXN_{i+1}"
    record = {
        "TXN_id" : transaction_id ,
        "order_id" : f"ORD_{i+1}" ,
        "merchant_id" : f"MER_{random.randint(1 , 100)}" ,
        "customer_id" : f"CUS_{random.randint(1 , 100)}" ,
        "amount" : round(random.uniform(10 , 10000) , 2) ,
        "currency" : "INR" , 
        "payment_method" : random.choice(PAYMENT_METHODS) ,
        "transaction_type" : random.choice(TRANSACTION_TYPES) ,
        "timestamp" : fake.date_time_between(start_date = "-30d" , end_date = "now")
    }
    GROUND_TRUTH.append(record)

GROUND_TRUTH = pd.DataFrame(GROUND_TRUTH)
# print(GROUND_TRUTH.head(5))

# Generate Source Dataset
SOURCES = ["GATEWAY" , "LEDGER" , "BANK"]
GATEWAY = GROUND_TRUTH.copy()
LEDGER = GROUND_TRUTH.copy()
BANK = GROUND_TRUTH.copy()

# Add source-specific IDs
GATEWAY["gateway_txn_id"] = [
    f"PAY_{fake.uuid4()}"
    for _ in range (len(GATEWAY))
]

LEDGER["ledger_txn_id"] = [
    f"LED_{fake.uuid4()}"
    for _ in range (len(LEDGER))
]

BANK["bank_txn_id"] = [
    f"UTR_{fake.uuid4()}"
    for _ in range (len(BANK))
]

# Source-specific statuses
GATEWAY["status"] = "SUCCESS"
LEDGER["status"] = "POSTED"
BANK["status"] = "CREDIT"

# Bank normally settles later than gateway/ledger
BANK["timestamp"] = BANK["timestamp"].apply(lambda x : x + timedelta(minutes = random.randint(1 , 60)))

# GATEWAY = GATEWAY[["gateway_txn_id" , "transaction_id" , "order_id" , "merchant_id" , "amount" , "currency" , "payment_method" , "transaction_type" , "status" , "timestamp"]]
# LEDGER = LEDGER[["ledger_txn_id" , "transaction_id" , "order_id" , "merchant_id" , "amount" , "currency" , "payment_method" , "transaction_type" , "status" , "timestamp"]]
# BANK = BANK[["bank_txn_id" , "transaction_id" , "merchant_id" , "amount" , "currency" , "transaction_type" , "status" , "timestamp"]]
