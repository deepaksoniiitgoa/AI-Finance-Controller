import pandas as pd

payment_method_canonical = {
    "UPI": "UPI",
    "UPI_PAYMENT": "UPI",
    "NET_BANKING": "NET_BANKING",
    "NETBANKING": "NET_BANKING",
    "CARD": "CARD",
    "DEBIT_CARD": "CARD",
    "WALLET": "WALLET",
    "E_WALLET": "WALLET",
}

def amount_match(a , b , tolerance):
    return abs(a["amount"] - b["amount"]) <= tolerance

def timestamp_match(a , b , max_minutes):
    return abs(a["timestamp"] - b["timestamp"]) <= pd.Timedelta(minutes=max_minutes)

def merchant_match(a , b):
    return a["merchant_id"] == b["merchant_id"]

def payment_method_match(a , b):
    PM1 = a["payment_method"]
    PM2 = b["payment_method"]
    return payment_method_canonical[PM1] == payment_method_canonical[PM2]

# Tier 1 matching (same amount , same time , same merchant)
def exact_match(source1 , source2):
    pairs = []
    for idx1 , row1 in source1.iterrows() :
        for idx2 , row2 in source2.iterrows() :
            same_amt = amount_match(row1 , row2 , tolerance=0)
            same_time = (row1["timestamp"].date() == row2["timestamp"].date())
            same_merchant = merchant_match(row1 , row2)
            if same_amt and same_merchant and same_time :
                pairs.append((idx1 , idx2))

    from collections import defaultdict
    a_to_b = defaultdict(list)
    b_to_a = defaultdict(list)

    for (idx1 , idx2) in pairs :
        a_to_b[idx1].append(idx2)
        b_to_a[idx2].append(idx1)

    matched = []
    ambiguous = []
    conflicts = []
    seen_b_conflicts = set()

    for idx1 , b_candidates in a_to_b.items() :
        if len(b_candidates) == 1 :
            idx2 = b_candidates[0]
            if len(b_to_a[idx2]) == 1 :
                matched.append({"idx1": idx1, "idx2": idx2})
            else:
                if idx2 not in seen_b_conflicts :
                    conflicts.append({"idx2": idx2, "candidates": b_to_a[idx2]})
                    seen_b_conflicts.add(idx2)
        else :
            ambiguous.append({"idx1": idx1, "candidates": b_candidates})
        
    a_pairs = set(a_to_b.keys())
    b_pairs = set(b_to_a.keys())
    unmatched1 = list(set(source1.index) - a_pairs)
    unmatched2 = list(set(source2.index) - b_pairs)

    return {
        "matched" : matched , 
        "ambiguous" : ambiguous ,
        "conflicts" : conflicts , 
        "unmatched1" : unmatched1 , 
        "unmatched2" : unmatched2 ,
    }

# Tier 2 matching (to catch th ebank fee payment i.e same time , same merchant and amount tolerance = 50)
def tolerant_match1(source1 , source2 , tolerance=50):
    pairs = []
    for idx1 , row1 in source1.iterrows() :
        for idx2 , row2 in source2.iterrows() :
            same_amt = amount_match(row1 , row2 , tolerance=tolerance)
            same_time = (row1["timestamp"].date() == row2["timestamp"].date())
            same_merchant = merchant_match(row1 , row2)
            if same_amt and same_merchant and same_time :
                pairs.append((idx1 , idx2))

    from collections import defaultdict
    a_to_b = defaultdict(list)
    b_to_a = defaultdict(list)

    for (idx1 , idx2) in pairs :
        a_to_b[idx1].append(idx2)
        b_to_a[idx2].append(idx1)

    matched = []
    ambiguous = []
    conflicts = []
    seen_b_conflicts = set()

    for idx1 , b_candidates in a_to_b.items() :
        if len(b_candidates) == 1 :
            idx2 = b_candidates[0]
            if len(b_to_a[idx2]) == 1 :
                matched.append({"idx1": idx1, "idx2": idx2})
            else:
                if idx2 not in seen_b_conflicts :
                    conflicts.append({"idx2": idx2, "candidates": b_to_a[idx2]})
                    seen_b_conflicts.add(idx2)
        else :
            ambiguous.append({"idx1": idx1, "candidates": b_candidates})
        
    a_pairs = set(a_to_b.keys())
    b_pairs = set(b_to_a.keys())
    unmatched1 = list(set(source1.index) - a_pairs)
    unmatched2 = list(set(source2.index) - b_pairs)

    return {
        "matched" : matched , 
        "ambiguous" : ambiguous ,
        "conflicts" : conflicts , 
        "unmatched1" : unmatched1 , 
        "unmatched2" : unmatched2 ,
    }

# Tier 3 matching (timestamp drift + firld variation)
def tolerant_match2(source1 , source2 , tolerance=50):
    pairs = []
    for idx1 , row1 in source1.iterrows() :
        for idx2 , row2 in source2.iterrows() :
            same_amt = amount_match(row1 , row2 , tolerance=tolerance)
            same_time = abs(row1["timestamp"] - row2["timestamp"]) <= pd.Timedelta(days=3)
            same_merchant = merchant_match(row1 , row2)
            if same_amt and same_merchant and same_time :
                pairs.append((idx1 , idx2))

    from collections import defaultdict
    a_to_b = defaultdict(list)
    b_to_a = defaultdict(list)

    for (idx1 , idx2) in pairs :
        a_to_b[idx1].append(idx2)
        b_to_a[idx2].append(idx1)

    matched = []
    ambiguous = []
    conflicts = []
    seen_b_conflicts = set()

    for idx1 , b_candidates in a_to_b.items() :
        if len(b_candidates) == 1 :
            idx2 = b_candidates[0]
            if len(b_to_a[idx2]) == 1 :
                matched.append({"idx1": idx1, "idx2": idx2})
            else:
                if idx2 not in seen_b_conflicts :
                    conflicts.append({"idx2": idx2, "candidates": b_to_a[idx2]})
                    seen_b_conflicts.add(idx2)
        else :
            ambiguous.append({"idx1": idx1, "candidates": b_candidates})
        
    a_pairs = set(a_to_b.keys())
    b_pairs = set(b_to_a.keys())
    unmatched1 = list(set(source1.index) - a_pairs)
    unmatched2 = list(set(source2.index) - b_pairs)

    return {
        "matched" : matched , 
        "ambiguous" : ambiguous ,
        "conflicts" : conflicts , 
        "unmatched1" : unmatched1 , 
        "unmatched2" : unmatched2 ,
    }


# ============================================================
# Union-Find (Disjoint Set Union) — for combining pairwise
# matches from all three source pairs into one 3-way picture
# ============================================================

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            self.parent[root_x] = root_y


def global_id(source_name, idx):
    return f"{source_name}_{idx}"


def source_of(gid):
    return gid.split("_")[0]


def apply_matches(uf, matches, source1_name, source2_name):
    for m in matches:
        id1 = global_id(source1_name, m["idx1"])
        id2 = global_id(source2_name, m["idx2"])
        uf.union(id1, id2)


def register_all_rows(uf, source_name, df):
    for idx in df.index:
        uf.find(global_id(source_name, idx))


def build_groups(uf, source_dfs):
    """
    source_dfs: dict like {"BANK": bank_df, "GATEWAY": gateway_df, "LEDGER": ledger_df}
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for source_name, df in source_dfs.items():
        for idx in df.index:
            gid = global_id(source_name, idx)
            root = uf.find(gid)
            groups[root].append(gid)
    return groups


def summarize_groups(groups):
    import pandas as pd
    group_summary = []
    for root, members in groups.items():
        sources_present = set(source_of(g) for g in members)
        group_summary.append({
            "root": root,
            "members": members,
            "num_sources": len(sources_present),
            "sources": sources_present
        })
    return pd.DataFrame(group_summary)