import pandas as pd
import data_generator
import exceptions
import matching

fake = data_generator.fake
GATEWAY = data_generator.GATEWAY
LEDGER = data_generator.LEDGER
BANK: pd.DataFrame = data_generator.BANK
PAYMENT_METHODS = data_generator.PAYMENT_METHODS
GROUND_TRUTH = data_generator.GROUND_TRUTH
INJECTION_LOG = exceptions.INJECTION_LOG

# DROP INDICES
already_dropped = []
GATEWAY , already_dropped = exceptions.drop_records(GATEWAY , "GATEWAY" , "gateway_txn_id" , already_dropped)
LEDGER , already_dropped = exceptions.drop_records(LEDGER , "LEDGER" , "ledger_txn_id" , already_dropped)
BANK , _ = exceptions.drop_records(BANK , "BANK" , "bank_txn_id" , already_dropped)

# Amount Mismatch in Bank
BANK = exceptions.amount_mismatch(BANK , "BANK" , "bank_txn_id")

# Timestamp Drift in Bank
BANK = exceptions.timestamp_drift(BANK , "BANK" , "bank_txn_id")

# Duplicate Entries in Gateway
GATEWAY = exceptions.add_duplicate_records(GATEWAY , "GATEWAY" , "gateway_txn_id")

# Orphan Records in Gateway
GATEWAY = exceptions.add_orphan_records(GATEWAY , "GATEWAY" , "gateway_txn_id")

# Field-level variation in Gateway
GATEWAY = exceptions.field_variation(GATEWAY , "GATEWAY" , "gateway_txn_id")


# which source record belongs to which true transaction.
GROUND_TRUTH_MAPPING = GROUND_TRUTH[["TXN_id"]].copy()
GROUND_TRUTH_MAPPING = GROUND_TRUTH_MAPPING.merge(GATEWAY[["TXN_id", "gateway_txn_id"]], on="TXN_id", how="left")
GROUND_TRUTH_MAPPING = GROUND_TRUTH_MAPPING.merge(LEDGER[["TXN_id", "ledger_txn_id"]], on="TXN_id", how="left")
GROUND_TRUTH_MAPPING = GROUND_TRUTH_MAPPING.merge(BANK[["TXN_id", "bank_txn_id"]], on="TXN_id", how="left")

GROUND_TRUTH_MAPPING.to_csv( "ground_truth_mapping.csv", index=False)

GATEWAY = GATEWAY.drop(columns=["TXN_id"])
LEDGER = LEDGER.drop(columns=["TXN_id"])
BANK = BANK.drop(columns=["TXN_id"])

GATEWAY = GATEWAY.reset_index(drop=True)
LEDGER = LEDGER.reset_index(drop=True)
BANK = BANK.reset_index(drop=True)

INJECTION_LOG = pd.DataFrame(INJECTION_LOG)

# Save Files
GROUND_TRUTH.to_csv( "ground_truth.csv", index=False)
GATEWAY.to_csv("gateway.csv", index=False)
LEDGER.to_csv("ledger.csv", index=False)
BANK.to_csv("bank.csv", index=False)
INJECTION_LOG.to_csv("injection_log.csv", index=False)

# Nramalization
COMMON_COLUMNS = [
    "source",
    "source_txn_id",
    "order_id",
    "customer_id",
    "merchant_id",
    "amount",
    "timestamp",
    "payment_method",
    "transaction_type",
    "status"
]

GATEWAY_NORM = pd.read_csv("./gateway.csv")
LEDGER_NORM = pd.read_csv("./ledger.csv")
BANK_NORM = pd.read_csv("./bank.csv")

GATEWAY_NORM = GATEWAY_NORM.rename(columns={"gateway_txn_id": "source_txn_id"})
GATEWAY_NORM["source"] = "GATEWAY"
GATEWAY_NORM = GATEWAY_NORM[COMMON_COLUMNS]

LEDGER_NORM = LEDGER_NORM.rename(columns={"ledger_txn_id": "source_txn_id"})
LEDGER_NORM["source"] = "LEDGER"
LEDGER_NORM = LEDGER_NORM[COMMON_COLUMNS]

BANK_NORM = BANK_NORM.rename(columns={"bank_txn_id": "source_txn_id"})
BANK_NORM["source"] = "BANK"
BANK_NORM = BANK_NORM[COMMON_COLUMNS]

ALL_TRANSACTIONS = pd.concat([GATEWAY_NORM , LEDGER_NORM , BANK_NORM] , ignore_index=True)
ALL_TRANSACTIONS["timestamp"] = pd.to_datetime(ALL_TRANSACTIONS["timestamp"])
ALL_TRANSACTIONS.to_csv("all_transactions.csv",index=False)

bank_df    = ALL_TRANSACTIONS[ALL_TRANSACTIONS["source"] == "BANK"]
gateway_df = ALL_TRANSACTIONS[ALL_TRANSACTIONS["source"] == "GATEWAY"]
ledger_df    = ALL_TRANSACTIONS[ALL_TRANSACTIONS["source"] == "LEDGER"]

# BANK - GATEWAY
bank_gateway_T1 = matching.exact_match(bank_df, gateway_df)
bank_gateway_T2 = matching.tolerant_match1(bank_df.loc[bank_gateway_T1["unmatched1"]], gateway_df.loc[bank_gateway_T1["unmatched2"]], tolerance=50)
bank_gateway_T3 = matching.tolerant_match2(bank_df.loc[bank_gateway_T2["unmatched1"]] , gateway_df.loc[bank_gateway_T2["unmatched2"]] , tolerance=50)

# BANK - LEDGER
bank_ledger_T1 = matching.exact_match(bank_df, ledger_df)
bank_ledger_T2 = matching.tolerant_match1(bank_df.loc[bank_ledger_T1["unmatched1"]], ledger_df.loc[bank_ledger_T1["unmatched2"]], tolerance=50)
bank_ledger_T3 = matching.tolerant_match2(bank_df.loc[bank_ledger_T2["unmatched1"]] , ledger_df.loc[bank_ledger_T2["unmatched2"]] , tolerance=50)

# GATEWAY - LEDGER
gateway_ledger_T1 = matching.exact_match(gateway_df, ledger_df)
gateway_ledger_T2 = matching.tolerant_match1(gateway_df.loc[gateway_ledger_T1["unmatched1"]], ledger_df.loc[gateway_ledger_T1["unmatched2"]], tolerance=50)
gateway_ledger_T3 = matching.tolerant_match2(gateway_df.loc[gateway_ledger_T2["unmatched1"]] , ledger_df.loc[gateway_ledger_T2["unmatched2"]] , tolerance=50)

# print(f"Tier 1 Matched: {len(gateway_ledger_T1['matched'])}")
# print(f"Tier 1 Ambiguous: {len(gateway_ledger_T1['ambiguous'])}")
# print(f"Tier 1 Conflicts: {len(gateway_ledger_T1['conflicts'])}")
# print(f"Tier 1 Unmatched1: {len(gateway_ledger_T1['unmatched1'])}")
# print(f"Tier 1 Unmatched2: {len(gateway_ledger_T1['unmatched2'])}")
# # print(gateway_ledger_T1["matched"])
# print(gateway_ledger_T1["conflicts"])
# print(f"Tier 2 Matched: {len(gateway_ledger_T2['matched'])}")
# print(f"Tier 2 Ambiguous: {len(gateway_ledger_T2['ambiguous'])}")
# print(f"Tier 2 Conflicts: {len(gateway_ledger_T2['conflicts'])}")
# print(f"Tier 2 Unmatched1: {len(gateway_ledger_T2['unmatched1'])}")
# print(f"Tier 2 Unmatched2: {len(gateway_ledger_T2['unmatched2'])}")
# print(f"Tier 3 Matched: {len(gateway_ledger_T3['matched'])}")
# print(f"Tier 3 Ambiguous: {len(gateway_ledger_T3['ambiguous'])}")
# print(f"Tier 3 Conflicts: {len(gateway_ledger_T3['conflicts'])}")
# print(f"Tier 3 Unmatched1: {len(gateway_ledger_T3['unmatched1'])}")
# print(f"Tier 3 Unmatched2: {len(gateway_ledger_T3['unmatched2'])}")

# sample_bank_id = "UTR_0a368ce7-dc57-4131-b8e1-daa7cbceabde"  # a real one tagged TIMESTAMP_DRIFT in injection_log, without also AMOUNT_MISMATCH
# sample_idx = bank_df[bank_df["source_txn_id"] == sample_bank_id].index[0]
# was_matched = any(m["idx1"] == sample_idx for m in result3["matched"])
# print(f"Known timestamp-drift matched at Tier 3: {was_matched}")

# def verify_match(idx1, idx2, source1_df, source2_df, mapping_df, id_col1, id_col2):
#     id1 = source1_df.loc[idx1, "source_txn_id"]
#     id2 = source2_df.loc[idx2, "source_txn_id"]

#     row1 = mapping_df[mapping_df[id_col1] == id1]
#     row2 = mapping_df[mapping_df[id_col2] == id2]

#     txn1 = row1["TXN_id"].values[0] if len(row1) else None
#     txn2 = row2["TXN_id"].values[0] if len(row2) else None

#     is_correct = (txn1 is not None) and (txn1 == txn2)
#     return {
#         "idx1": idx1, "idx2": idx2,
#         "id1": id1, "id2": id2,
#         "txn1": txn1, "txn2": txn2,
#         "correct": is_correct
#     }

# mapping = pd.read_csv("ground_truth_mapping.csv")
# verification_results = []
# for m in result3["matched"]:
#     res = verify_match(
#         m["idx1"], m["idx2"],
#         bank_df, gateway_df,
#         mapping,
#         "bank_txn_id", "gateway_txn_id"
#     )
#     verification_results.append(res)

# verification_df = pd.DataFrame(verification_results)
# print(verification_df["correct"].value_counts()

# mapping = pd.read_csv("ground_truth_mapping.csv")
# # pick a couple from result1["matched"], e.g. the first one
# m = bank_gateway_T1["matched"][29]
# idx1, idx2 = m["idx1"], m["idx2"]

# bank_id = bank_df.loc[idx1, "source_txn_id"]
# gateway_id = gateway_df.loc[idx2, "source_txn_id"]

# print(mapping[mapping["bank_txn_id"] == bank_id][["TXN_id", "bank_txn_id"]])
# print(mapping[mapping["gateway_txn_id"] == gateway_id][["TXN_id", "gateway_txn_id"]])

# ============================================================
# Combine all three pairwise results into one 3-way
# picture using union-find
# ============================================================

uf = matching.UnionFind()

matching.apply_matches(uf, bank_gateway_T1["matched"], "BANK", "GATEWAY")
matching.apply_matches(uf, bank_gateway_T2["matched"], "BANK", "GATEWAY")
matching.apply_matches(uf, bank_gateway_T3["matched"], "BANK", "GATEWAY")

matching.apply_matches(uf, bank_ledger_T1["matched"], "BANK", "LEDGER")
matching.apply_matches(uf, bank_ledger_T2["matched"], "BANK", "LEDGER")
matching.apply_matches(uf, bank_ledger_T3["matched"], "BANK", "LEDGER")

matching.apply_matches(uf, gateway_ledger_T1["matched"], "GATEWAY", "LEDGER")
matching.apply_matches(uf, gateway_ledger_T2["matched"], "GATEWAY", "LEDGER")
matching.apply_matches(uf, gateway_ledger_T3["matched"], "GATEWAY", "LEDGER")

matching.register_all_rows(uf, "BANK", bank_df)
matching.register_all_rows(uf, "GATEWAY", gateway_df)
matching.register_all_rows(uf, "LEDGER", ledger_df)

source_dfs = {"BANK": bank_df, "GATEWAY": gateway_df, "LEDGER": ledger_df}
groups = matching.build_groups(uf, source_dfs)
summary_df = matching.summarize_groups(groups)

print(f"Total groups: {len(summary_df)}")
print(summary_df["num_sources"].value_counts())

summary_df.to_csv("reconciliation_groups.csv", index=False)

# ============================================================
# Categorize every unresolved group with a specific,
# honest exception reason
# ============================================================

# Collect ambiguous/conflict entries from every tier of every pair,
# tagged with which pair and which sources they involve
all_ambiguous_conflicts = []

def collect_ambiguity(entries, kind, source1_name, source2_name, key_field):
    for e in entries:
        all_ambiguous_conflicts.append({
            "kind": kind,                      # "AMBIGUOUS" or "CONFLICT"
            "source1": source1_name,
            "source2": source2_name,
            "anchor_idx": e[key_field],
            "candidates": e["candidates"]
        })

for pair_name, (s1, s2, t1, t2, t3) in {
    "BANK_GATEWAY": ("BANK", "GATEWAY", bank_gateway_T1, bank_gateway_T2, bank_gateway_T3),
    "BANK_LEDGER": ("BANK", "LEDGER", bank_ledger_T1, bank_ledger_T2, bank_ledger_T3),
    "GATEWAY_LEDGER": ("GATEWAY", "LEDGER", gateway_ledger_T1, gateway_ledger_T2, gateway_ledger_T3),
}.items():
    for tier_result in [t1, t2, t3]:
        collect_ambiguity(tier_result["ambiguous"], "AMBIGUOUS", s1, s2, "idx1")
        collect_ambiguity(tier_result["conflicts"], "CONFLICT", s1, s2, "idx2")

ambiguity_df = pd.DataFrame(all_ambiguous_conflicts)
ambiguity_df.to_csv("ambiguity_conflict_log.csv", index=False)
print(f"Total ambiguous/conflict entries logged: {len(ambiguity_df)}")


def classify_exception(row):
    n = row["num_sources"]
    if n == 3:
        return "FULLY_MATCHED"
    elif n == 2:
        return "MISSING_FROM_ONE_SOURCE"
    else:
        return "NO_CANDIDATE_FOUND"

summary_df["status"] = summary_df.apply(classify_exception, axis=1)

def missing_source(row):
    if row["num_sources"] == 2:
        present = set(matching.source_of(g) for g in row["members"])
        all_sources = {"BANK", "GATEWAY", "LEDGER"}
        missing = all_sources - present
        return list(missing)[0] if missing else None
    return None

summary_df["missing_source"] = summary_df.apply(missing_source, axis=1)

print(summary_df["status"].value_counts())
summary_df.to_csv("reconciliation_groups.csv", index=False)

# ============================================================
# Validate the combined result against ground truth
# ============================================================

mapping = pd.read_csv("ground_truth_mapping.csv")

def get_txn_id(gid):
    src, idx = gid.split("_", 1)
    idx = int(idx)
    if src == "BANK":
        source_txn_id = bank_df.loc[idx, "source_txn_id"]
        row = mapping[mapping["bank_txn_id"] == source_txn_id]
    elif src == "GATEWAY":
        source_txn_id = gateway_df.loc[idx, "source_txn_id"]
        row = mapping[mapping["gateway_txn_id"] == source_txn_id]
    else:
        source_txn_id = ledger_df.loc[idx, "source_txn_id"]
        row = mapping[mapping["ledger_txn_id"] == source_txn_id]
    return row["TXN_id"].values[0] if len(row) else None

def group_is_correct(members):
    txn_ids = set(get_txn_id(m) for m in members)
    txn_ids.discard(None)
    return len(txn_ids) <= 1   # all members trace to the same TXN_id (or unresolvable orphans)

summary_df["is_correct"] = summary_df["members"].apply(group_is_correct)
print(summary_df["is_correct"].value_counts())

precision = summary_df["is_correct"].mean()
print(f"Overall group precision: {precision:.2%}")

# ============================================================
# Final report
# ============================================================

total_true_transactions = len(GROUND_TRUTH)
fully_matched = (summary_df["status"] == "FULLY_MATCHED").sum()
partial = (summary_df["status"] == "MISSING_FROM_ONE_SOURCE").sum()
orphans = (summary_df["status"] == "NO_CANDIDATE_FOUND").sum()

match_rate = fully_matched / total_true_transactions

report_lines = [
    "# Reconciliation Report",
    "",
    f"**Total ground-truth transactions:** {total_true_transactions}",
    f"**Fully matched (3/3 sources):** {fully_matched}",
    f"**Partially matched (2/3 sources):** {partial}",
    f"**Unresolved (1/3, orphans/exceptions):** {orphans}",
    f"**Match rate:** {match_rate:.2%}",
    f"**Group precision (validated against ground truth):** {precision:.2%}",
    "",
    "## Ambiguous / Conflict Cases",
    f"Total flagged for manual review: {len(ambiguity_df)}",
    "",
    "## Exception Details",
    "See `reconciliation_groups.csv` and `ambiguity_conflict_log.csv` for full records.",
]

with open("reconciliation_report.md", "w") as f:
    f.write("\n".join(report_lines))

print("\n".join(report_lines))

