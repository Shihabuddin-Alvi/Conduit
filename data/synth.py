import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Column:
    name: str
    dtype: str
    value_generator: Callable[[], Any]

def base_schema():
    return [
        Column(
            name="id",
            dtype="int",
            value_generator=lambda: random.randint(1, 9999)
        ),
        Column(
            name="name",
            dtype="str",
            value_generator=lambda: random.choice(["Lionel Messi", "Cristiano Ronaldo", "Bob Allen", "Alice Williams", "Charlie Brown", "Diana Ross", "Edward Chen", "Fiona Garcia"])
        ),
        Column(
            name="email",
            dtype="str",
            value_generator=lambda: f"user{random.randint(1, 999)}@example.com"
        ),
        Column(
            name="address_line_1",
            dtype="str",
            value_generator=lambda: f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Cedar Ln', 'Maple Dr', 'Birch Blvd'])}"
        ),
        Column(
            name="address_line_2",
            dtype="str",
            value_generator=lambda: "" if random.random() < 0.7 else random.choice([f"Apt {random.randint(1, 50)}", f"Suite {random.randint(100, 500)}", f"Unit {random.randint(1, 20)}"])
        ),
        Column(
            name="created_at",
            dtype="datetime",
            value_generator=lambda: datetime.now() - timedelta(days=random.randint(0, 365))
        ),
        Column(
            name="amount",
            dtype="float",
            value_generator=lambda: round(random.uniform(10.0, 1000.0), 2)
        ),
        Column(
            name="status",
            dtype="str",
            value_generator=lambda: random.choice(["active", "inactive", "pending", "suspended"])
        )
    ]

ABBREVIATIONS = {
    "address": "addr",
    "customer": "cust",
    "created": "crtd",
    "amount": "amt",
    "status": "stat",
    "email": "eml"
}

def apply_abbreviations(schema):
    new_schema = []
    mapping = {}
    
    for col in schema:
        parts = col.name.split("_")
        new_parts = [ABBREVIATIONS.get(part, part) for part in parts]
        new_name = "_".join(new_parts).upper()
        
        new_col = Column(
            name=new_name,
            dtype=col.dtype,
            value_generator=col.value_generator
        )
        
        new_schema.append(new_col)
        mapping[col.name] = new_name
    
    return new_schema, mapping

def apply_strip_vowels(schema):
    new_schema = []
    mapping = {}
    vowels = "aeiou"
    
    for col in schema:
        parts = col.name.split("_")
        new_parts = []
        for part in parts:
            no_vowels = "".join(char for char in part if char.lower() not in vowels)
            new_parts.append(no_vowels)
        new_name = "_".join(new_parts).upper()
        
        new_col = Column(
            name=new_name,
            dtype=col.dtype,
            value_generator=col.value_generator
        )
        
        new_schema.append(new_col)
        mapping[col.name] = new_name
    
    return new_schema, mapping

def apply_table_prefix(schema, table_code="CUST"):
    new_schema = []
    mapping = {}
    
    for col in schema:
        new_name = f"{table_code}_{col.name}".upper()
        new_col = Column(
            name=new_name,
            dtype=col.dtype,
            value_generator=col.value_generator
        )
        new_schema.append(new_col)
        mapping[col.name] = new_name
    
    return new_schema, mapping

def apply_date_format(schema):
    new_schema = []
    mapping = {}
    
    for col in schema:
        if col.dtype == "datetime":
            old_gen = col.value_generator
            
            def new_gen():
                dt = old_gen()
                return int(dt.strftime("%Y%m%d"))
            
            new_col = Column(
                name=col.name,
                dtype="int",
                value_generator=new_gen
            )
        else:
            new_col = Column(
                name=col.name,
                dtype=col.dtype,
                value_generator=col.value_generator
            )
        
        new_schema.append(new_col)
        mapping[col.name] = col.name
    
    return new_schema, mapping

def apply_split_field(schema, original_to_current=None):
    original_to_current = original_to_current or {}
    current_name = original_to_current.get("name", "name")
    
    new_schema = []
    mapping = {}
    
    for col in schema:
        if col.name == current_name:
            name_gen = col.value_generator
            new_col1 = Column(
                name="NAME1",
                dtype="str",
                value_generator=lambda gen=name_gen: gen().split()[0]
            )
            new_col2 = Column(
                name="NAME2",
                dtype="str",
                value_generator=lambda gen=name_gen: gen().split()[-1] if len(gen().split()) > 1 else ""
            )
            new_schema.append(new_col1)
            new_schema.append(new_col2)
            mapping["name"] = ["NAME1", "NAME2"]
        else:
            new_schema.append(col)
            mapping[col.name] = col.name
    
    return new_schema, mapping

def apply_merge_fields(schema, original_to_current=None):
    original_to_current = original_to_current or {}
    addr1_current = original_to_current.get("address_line_1", "address_line_1")
    addr2_current = original_to_current.get("address_line_2", "address_line_2")
    
    new_schema = []
    mapping = {}
    merged = set()
    
    addr2 = next((c for c in schema if c.name == addr2_current), None)
    
    for col in schema:
        if col.name in merged:
            continue
        if col.name == addr1_current and addr2:
            g1, g2 = col.value_generator, addr2.value_generator
            new_schema.append(Column(
                "STRAS", "str",
                lambda g1=g1, g2=g2: f"{g1()}, {g2()}" if g2() else g1()
            ))
            mapping.update({"address_line_1": "STRAS", "address_line_2": "STRAS"})
            merged.update([col.name, addr2.name])
        else:
            new_schema.append(Column(col.name, col.dtype, col.value_generator))
            mapping[col.name] = col.name
    
    return new_schema, mapping

def apply_unit_change(schema):
    new_schema = []
    mapping = {}
    
    for col in schema:
        if col.name == "amount":
            old_gen = col.value_generator
            
            def new_gen():
                return int(old_gen() * 100)
            
            new_col = Column(
                name=col.name,
                dtype="int",
                value_generator=new_gen
            )
        else:
            new_col = Column(
                name=col.name,
                dtype=col.dtype,
                value_generator=col.value_generator
            )
        
        new_schema.append(new_col)
        mapping[col.name] = col.name
    
    return new_schema, mapping

def apply_case_flip(schema):
    new_schema = []
    mapping = {}
    
    for col in schema:
        new_name = col.name.upper()
        new_col = Column(
            name=new_name,
            dtype=col.dtype,
            value_generator=col.value_generator
        )
        new_schema.append(new_col)
        mapping[col.name] = new_name
    
    return new_schema, mapping

OPERATORS = {
    "abbreviate": apply_abbreviations,
    "strip_vowels": apply_strip_vowels,
    "table_prefix": apply_table_prefix,
    "date_format": apply_date_format,
    "split_field": apply_split_field,
    "merge_fields": apply_merge_fields,
    "unit_change": apply_unit_change,
    "case_flip": apply_case_flip,
}

def generate_legacy_pair(schema, operators):
    current_schema = schema
    ground_truth = []  # list of (orig, final) pairs
    
    for op_name in operators:
        func = OPERATORS[op_name]
        current_schema, step_mapping = func(current_schema)
        
        if op_name == "unit_change":
            for c in current_schema:
                if "amount" in c.name.lower() or "amt" in c.name.lower() or "mt" == c.name.lower():
                    print(f"DEBUG after unit_change: {c.name} dtype={c.dtype}")
        
        # Convert step_mapping to a list of (orig, new) pairs
        pairs = []
        if isinstance(step_mapping, dict):
            for orig, new in step_mapping.items():
                if isinstance(new, list):
                    for target in new:
                        pairs.append((orig, target))
                else:
                    pairs.append((orig, new))
        else:
            pairs = step_mapping
        
        # Merge pairs into ground_truth
        for step_orig, step_new in pairs:
            found = False
            for idx, (orig, current) in enumerate(ground_truth):
                if current == step_orig:
                    ground_truth[idx] = (orig, step_new)
                    found = True
            if not found:
                ground_truth.append((step_orig, step_new))
    
    return current_schema, ground_truth

def apply_add_junk(schema):
    new_schema = list(schema)
    mapping = {col.name: col.name for col in schema}

    junk_cols = [
        Column(
            name="LEGACY_FLAG",
            dtype="int",
            value_generator=lambda: random.randint(0, 1),
        ),
        Column(
            name="INTERNAL_CODE",
            dtype="str",
            value_generator=lambda: random.choice(
                ["A102", "B205", "C307", "X999"]
            ),
        ),
        Column(
            name="MIGRATION_BATCH",
            dtype="str",
            value_generator=lambda: random.choice(
                ["batch_01", "batch_02", "batch_03"]
            ),
        ),
    ]

    new_schema.extend(junk_cols)

    return new_schema, mapping

def apply_drop_column(schema):
    new_schema = []
    mapping = {}
    
    cols_to_drop = ["status"]

    for col in schema:
        if col.name not in cols_to_drop:
            new_schema.append(col)
            mapping[col.name] = col.name

    return new_schema, mapping

if __name__ == "__main__":
    clean_schema = base_schema()
    
    # Drop status before any renaming happens
    clean_schema, _ = apply_drop_column(clean_schema)
    
    operators_list = ["split_field", "merge_fields", "unit_change", "date_format", 
                      "abbreviate", "strip_vowels", "table_prefix", "case_flip"]
    
    final_schema, ground_truth = generate_legacy_pair(clean_schema, operators_list)
    
    before_names = {c.name for c in final_schema}
    
    final_schema, _ = apply_add_junk(final_schema)
    
    new_names = [c.name for c in final_schema if c.name not in before_names]
    for name in new_names:
        ground_truth.append((None, name))
    
    print("FINAL SCHEMA:")
    for col in final_schema:
        print(f"  {col.name} ({col.dtype})")
    
    print("\nGROUND TRUTH:")
    for orig, final in ground_truth:
        print(f"  {orig} -> {final}")
    
    print("\nSAMPLE ROWS:")
    for i in range(5):
        row = {col.name: col.value_generator() for col in final_schema}
        print(f"  Row {i+1}: {row}")