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

if __name__ == "__main__":
    schema = base_schema()
    new_schema, mapping = apply_strip_vowels(schema)
    for orig, new in mapping.items():
        print(orig, "->", new)

OPERATORS = {
    "abbreviate": apply_abbreviations,
    "strip_vowels": apply_strip_vowels,
}

def generate_legacy_pair(schema, operators):
    current_schema = schema
    combined_mapping = {}
    
    for op_name in operators:
        func = OPERATORS[op_name]
        current_schema, step_mapping = func(current_schema)
        
        for step_orig, step_new in step_mapping.items():
            found = False
            for orig_name, current_name in combined_mapping.items():
                if current_name == step_orig:
                    combined_mapping[orig_name] = step_new
                    found = True
                    break
            if not found:
                combined_mapping[step_orig] = step_new
    
    return current_schema, combined_mapping

if __name__ == "__main__":
    schema = base_schema()
    final_schema, combined_mapping = generate_legacy_pair(schema, ["abbreviate", "strip_vowels"])
    
    for orig, final in combined_mapping.items():
        print(f"{orig:20} -> {final}")