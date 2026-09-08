import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Optional

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

def apply_abbreviations(schema, original_to_current=None):
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

def apply_strip_vowels(schema, original_to_current=None):
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

def apply_table_prefix(schema, original_to_current=None, table_code="CUST"):
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

def apply_date_format(schema, original_to_current=None):
    new_schema = []
    mapping = {}
    
    for col in schema:
        if col.dtype == "datetime":
            old_gen = col.value_generator
            
            def new_gen(old_gen=old_gen):
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
    # Determine current name for the original "name" column
    current_names = original_to_current.get("name", ["name"]) if original_to_current else ["name"]
    current_name = current_names[0]  # assume only one current name
    
    new_schema = []
    mapping = {}
    
    for col in schema:
        if col.name == current_name:
            name_gen = col.value_generator

            def name1_gen(gen=name_gen):
                return gen().split()[0]

            def name2_gen(gen=name_gen):
                parts = gen().split()
                return parts[-1] if len(parts) > 1 else ""
            
            new_col1 = Column(
                name="NAME1",
                dtype="str",
                value_generator=name1_gen
            )
            new_col2 = Column(
                name="NAME2",
                dtype="str",
                value_generator=name2_gen
            )
            new_schema.append(new_col1)
            new_schema.append(new_col2)
            # Map the current name (the one being split) to the two new names
            mapping[col.name] = ["NAME1", "NAME2"]
        else:
            new_schema.append(col)
            mapping[col.name] = col.name
    
    return new_schema, mapping

def apply_merge_fields(schema, original_to_current=None):
    # Determine current names for the original address columns
    if original_to_current:
        addr1_current = original_to_current.get("address_line_1", ["address_line_1"])[0]
        addr2_current = original_to_current.get("address_line_2", ["address_line_2"])[0]
    else:
        addr1_current = "address_line_1"
        addr2_current = "address_line_2"
    
    new_schema = []
    mapping = {}
    merged = set()
    
    addr2 = next((c for c in schema if c.name == addr2_current), None)
    
    for col in schema:
        if col.name in merged:
            continue
        if col.name == addr1_current and addr2:
            g1, g2 = col.value_generator, addr2.value_generator

            def merged_gen(g1=g1, g2=g2):
                addr1 = g1()
                addr2 = g2()
                if addr2:
                    return f"{addr1}, {addr2}"
                return addr1

            new_schema.append(Column(
                "STRAS", "str",
                merged_gen
            ))
            mapping.update({addr1_current: "STRAS", addr2_current: "STRAS"})
            merged.update([col.name, addr2.name])
        else:
            new_schema.append(Column(col.name, col.dtype, col.value_generator))
            mapping[col.name] = col.name
    
    return new_schema, mapping

def apply_unit_change(schema, original_to_current=None):
    new_schema = []
    mapping = {}
    
    for col in schema:
        if col.name == "amount":
            old_gen = col.value_generator
            
            def new_gen(old_gen=old_gen):
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

def apply_case_flip(schema, original_to_current=None):
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

def apply_add_junk(schema, original_to_current=None):
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
    # Map None to all junk column names (they have no original)
    mapping[None] = [col.name for col in junk_cols]

    return new_schema, mapping

def apply_drop_column(schema, original_to_current=None):
    new_schema = []
    mapping = {}
    
    cols_to_drop = ["status"]

    for col in schema:
        if col.name not in cols_to_drop:
            new_schema.append(col)
            mapping[col.name] = col.name

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
    "add_junk": apply_add_junk,
    "drop_column": apply_drop_column,
}

def generate_legacy_pair(schema, operators):
    current_schema = schema
    ground_truth = []  # list of (orig, final) pairs
    
    # Maintain mapping from original column names to list of current names
    original_to_current = {col.name: [col.name] for col in schema}
    
    for op_name in operators:
        func = OPERATORS[op_name]
        # Pass original_to_current to operators that need it
        current_schema, step_mapping = func(current_schema, original_to_current)
        
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
        
        # Update original_to_current based on step_mapping
        # Only consider keys that are actual column names (not None)
        for old_name, new_names in step_mapping.items():
            if old_name is None:
                continue
            # Convert new_names to list for uniform handling
            if not isinstance(new_names, list):
                new_names = [new_names]
            # Update each original that currently maps to old_name
            for orig, current_list in original_to_current.items():
                if old_name in current_list:
                    # Replace old_name with the new names
                    idx = current_list.index(old_name)
                    current_list[idx:idx+1] = new_names
                    # Remove duplicates if any (not necessary)
    
    return current_schema, ground_truth

if __name__ == "__main__":
    clean_schema = base_schema()
    
    operators_list = [
        "drop_column",
        "split_field",
        "merge_fields",
        "unit_change",
        "date_format",
        "abbreviate",
        "strip_vowels",
        "table_prefix",
        "case_flip",
        "add_junk"
    ]
    
    final_schema, ground_truth = generate_legacy_pair(clean_schema, operators_list)
    
print("FINAL SCHEMA:")
for col in final_schema:
    print(f"  {col.name} ({col.dtype})")

print("\nSOURCE SCHEMA (original):", [c.name for c in clean_schema])
print("TARGET SCHEMA (final):", [c.name for c in final_schema])

print("\nGROUND TRUTH:")
for orig, final in ground_truth:
    print(f"  {orig} -> {final}")

print("\nSAMPLE ROWS:")
for i in range(5):
    row = {col.name: col.value_generator() for col in final_schema}
    print(f"  Row {i+1}: {row}")