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
        if col.name == current_name:  # Use current_name, not "name"
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
    original_names = [col.name for col in schema]
    
    for op_name in operators:
        func = OPERATORS[op_name]
        if op_name in ["split_field", "merge_fields"]:
            current_schema, _ = func(current_schema, {col.name: col.name for col in current_schema})
        else:
            current_schema, _ = func(current_schema)
    
    # Build ground truth: map original column names to final column names
    # Based on what the operators do
    ground_truth = []
    final_names = {col.name for col in current_schema}
    
    # Manually encode the mappings based on operators
    if "split_field" in operators:
        ground_truth.extend([("name", "NAME1"), ("name", "NAME2")])
    if "merge_fields" in operators:
        ground_truth.extend([("address_line_1", "STRAS"), ("address_line_2", "STRAS")])
    
    # For other columns, build the expected final name
    for orig in original_names:
        if orig in ["name", "address_line_1", "address_line_2"]:
            continue  # Already handled
        # Trace the transformations
        final = orig
        if "abbreviate" in operators:
            parts = final.split("_")
            new_parts = [ABBREVIATIONS.get(part, part) for part in parts]
            final = "_".join(new_parts)
        if "strip_vowels" in operators:
            parts = final.split("_")
            new_parts = ["".join(c for c in part if c.lower() not in "aeiou") for part in parts]
            final = "_".join(new_parts)
        if "table_prefix" in operators:
            final = f"CUST_{final}"
        if "case_flip" in operators:
            final = final.upper()
        
        ground_truth.append((orig, final))
    
    return current_schema, ground_truth

def apply_structural_changes(schema, ground_truth, add_junk_count=3, drop_columns=None):
    new_schema = list(schema)
    new_ground_truth = list(ground_truth)
    
    if drop_columns is None:
        drop_columns = ["status"]
    
    # Drop columns from schema and ground_truth
    for col_name in drop_columns:
        new_schema = [c for c in new_schema if c.name != col_name]
        new_ground_truth = [(src, tgt) for src, tgt in new_ground_truth if src != col_name and tgt != col_name]
    
    # Add junk columns
    junk_names = ["LEGACY_FLAG", "INTERNAL_CODE", "MIGRATION_BATCH"]
    junk_generators = [
        lambda: random.randint(0, 1),
        lambda: random.choice(["A102", "B205", "C307", "X999"]),
        lambda: random.choice(["batch_01", "batch_02", "batch_03"])
    ]
    
    for i in range(add_junk_count):
        junk_col = Column(
            name=junk_names[i] if i < len(junk_names) else f"JUNK_{i}",
            dtype="str" if i > 0 else "int",
            value_generator=junk_generators[i] if i < len(junk_generators) else lambda: "junk"
        )
        new_schema.append(junk_col)
        new_ground_truth.append((None, junk_col.name))
    
    return new_schema, new_ground_truth

def apply_operators_to_values(clean_values, operators_list):
    legacy_values = []
    
    for row in clean_values:
        legacy_row = dict(row)
        key_mapping = {k: k for k in row.keys()}
        
        for op_name in operators_list:
            if op_name == "abbreviate":
                new_row = {}
                new_mapping = {}
                for col_name, val in legacy_row.items():
                    parts = col_name.split("_")
                    new_parts = [ABBREVIATIONS.get(part, part) for part in parts]
                    new_name = "_".join(new_parts).upper()
                    new_row[new_name] = val
                    for orig, current in key_mapping.items():
                        if current == col_name:
                            new_mapping[orig] = new_name
                            break
                legacy_row = new_row
                key_mapping = new_mapping
            
            elif op_name == "strip_vowels":
                vowels = "aeiou"
                new_row = {}
                new_mapping = {}
                for col_name, val in legacy_row.items():
                    parts = col_name.split("_")
                    new_parts = ["".join(c for c in part if c.lower() not in vowels) for part in parts]
                    new_name = "_".join(new_parts).upper()
                    new_row[new_name] = val
                    for orig, current in key_mapping.items():
                        if current == col_name:
                            new_mapping[orig] = new_name
                            break
                legacy_row = new_row
                key_mapping = new_mapping
            
            elif op_name == "table_prefix":
                new_row = {}
                new_mapping = {}
                for col_name, val in legacy_row.items():
                    new_name = f"CUST_{col_name}".upper()
                    new_row[new_name] = val
                    for orig, current in key_mapping.items():
                        if current == col_name:
                            new_mapping[orig] = new_name
                            break
                legacy_row = new_row
                key_mapping = new_mapping
            
            elif op_name == "date_format":
                current_name = key_mapping.get("created_at", "created_at")
                if current_name in legacy_row:
                    dt = legacy_row[current_name]
                    if isinstance(dt, datetime):
                        legacy_row[current_name] = int(dt.strftime("%Y%m%d"))
            
            elif op_name == "split_field":
                current_name = key_mapping.get("name", "name")
                if current_name in legacy_row:
                    name_parts = legacy_row[current_name].split()
                    legacy_row["NAME1"] = name_parts[0] if len(name_parts) > 0 else ""
                    legacy_row["NAME2"] = name_parts[-1] if len(name_parts) > 1 else ""
                    del legacy_row[current_name]
                    key_mapping.pop("name", None)
                    key_mapping["NAME1"] = "NAME1"
                    key_mapping["NAME2"] = "NAME2"
            
            elif op_name == "merge_fields":
                addr1_key = key_mapping.get("address_line_1", "address_line_1")
                addr2_key = key_mapping.get("address_line_2", "address_line_2")
                if addr1_key in legacy_row:
                    addr1 = legacy_row.get(addr1_key, "")
                    addr2 = legacy_row.get(addr2_key, "")
                    legacy_row["STRAS"] = f"{addr1}, {addr2}" if addr2 else addr1
                    del legacy_row[addr1_key]
                    if addr2_key in legacy_row:
                        del legacy_row[addr2_key]
                    key_mapping.pop("address_line_1", None)
                    key_mapping.pop("address_line_2", None)
                    key_mapping["STRAS"] = "STRAS"
            
            elif op_name == "unit_change":
                current_name = key_mapping.get("amount", "amount")
                if current_name in legacy_row:
                    legacy_row[current_name] = int(legacy_row[current_name] * 100)
            
            elif op_name == "case_flip":
                new_row = {}
                new_mapping = {}
                for col_name, val in legacy_row.items():
                    new_name = col_name.upper()
                    new_row[new_name] = val
                    for orig, current in key_mapping.items():
                        if current == col_name:
                            new_mapping[orig] = new_name
                            break
                legacy_row = new_row
                key_mapping = new_mapping
        
        legacy_values.append(legacy_row)
    
    return legacy_values

if __name__ == "__main__":
    # Generate clean schema and data
    clean_schema = base_schema()
    
    # Generate clean values for 10 rows
    clean_values = []
    for _ in range(10):
        row = {col.name: col.value_generator() for col in clean_schema}
        clean_values.append(row)
    
    # Apply all operators to get legacy schema and ground truth
    operators_list = ["abbreviate", "strip_vowels", "table_prefix", "date_format", 
                      "split_field", "merge_fields", "unit_change", "case_flip"]
    legacy_schema, ground_truth = generate_legacy_pair(clean_schema, operators_list)
    
    # Apply structural changes (add junk, drop columns)
    legacy_schema, ground_truth = apply_structural_changes(
        legacy_schema, ground_truth, add_junk_count=3, drop_columns=["status"]
    )
    
    # Transform values
    legacy_values = apply_operators_to_values(clean_values, operators_list)
    
    # Print results
    print("SOURCE COLUMNS (clean):")
    for col in clean_schema:
        print(f"  {col.name} ({col.dtype})")
    
    print("\nTARGET COLUMNS (legacy):")
    for col in legacy_schema:
        print(f"  {col.name} ({col.dtype})")
    
    print("\nGROUND TRUTH (clean -> legacy):")
    for src, tgt in ground_truth:
        print(f"  {src} -> {tgt}")
    
    print("\nDATA (first 10 rows):")
    for i, row in enumerate(legacy_values[:10]):
        print(f"  Row {i+1}: {row}")