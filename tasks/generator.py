"""
Procedural dirty data generator with error injection.
Generates CSV tasks with controllable difficulty and seed-based reproducibility.
"""

import csv
import io
import random
from typing import Dict, List, Optional

# ============================================================
# Data pools
# ============================================================

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
    "Ivy", "Jack", "Karen", "Leo", "Mia", "Noah", "Olivia", "Paul",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zane", "Aiden", "Bella", "Caleb", "Daisy",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Indianapolis", "Charlotte", "Seattle", "Denver",
    "Boston", "Nashville",
]

PRODUCTS = [
    "Wireless Mouse", "USB Keyboard", "Monitor Stand", "Webcam HD",
    "Laptop Sleeve", "Power Bank", "Bluetooth Speaker", "LED Desk Lamp",
    "Noise Cancelling Headphones", "Portable SSD", "USB Hub", "HDMI Cable",
    "Ergonomic Chair", "Standing Desk", "Mechanical Keyboard", "Graphics Tablet",
    "External DVD Drive", "Surge Protector", "Cable Organizer", "Desk Mat",
]

CATEGORIES = [
    "Electronics", "Furniture", "Accessories", "Storage", "Audio",
    "Peripherals", "Cables", "Lighting", "Computing", "Office Supplies",
]

STATUSES = ["Active", "Inactive", "Pending", "Completed", "Cancelled"]

REGIONS = ["North", "South", "East", "West", "Central"]

DEPARTMENTS = [
    "Sales", "Marketing", "Engineering", "Support", "Finance",
    "HR", "Operations", "Legal", "Product", "Design",
]

# ============================================================
# Column templates
# ============================================================

COLUMN_TEMPLATES = {
    "customer": {
        "columns": ["customer_id", "first_name", "last_name", "email", "signup_date", "city", "region", "status"],
        "types": {
            "customer_id": "integer",
            "first_name": "string",
            "last_name": "string",
            "email": "string",
            "signup_date": "date_yyyy_mm_dd",
            "city": "string",
            "region": "category",
            "status": "category",
        },
    },
    "orders": {
        "columns": ["order_id", "customer_name", "order_date", "product", "quantity", "unit_price", "total", "department"],
        "types": {
            "order_id": "integer",
            "customer_name": "string",
            "order_date": "date_yyyy_mm_dd",
            "product": "string",
            "quantity": "integer",
            "unit_price": "float",
            "total": "float",
            "department": "category",
        },
    },
    "products": {
        "columns": ["product_id", "product_name", "category", "price", "in_stock", "rating", "release_date", "status"],
        "types": {
            "product_id": "integer",
            "product_name": "string",
            "category": "category",
            "price": "float",
            "in_stock": "boolean",
            "rating": "float",
            "release_date": "date_yyyy_mm_dd",
            "status": "category",
        },
    },
}

# ============================================================
# Clean data generation
# ============================================================


def _generate_clean_row(template_name: str, row_idx: int, rng: random.Random) -> Dict[str, str]:
    """Generate one clean row for the given template."""
    tmpl = COLUMN_TEMPLATES[template_name]
    types = tmpl["types"]
    row = {}

    if template_name == "customer":
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        row["customer_id"] = str(1000 + row_idx)
        row["first_name"] = first
        row["last_name"] = last
        row["email"] = f"{first.lower()}.{last.lower()}@example.com"
        row["signup_date"] = _random_date(rng)
        row["city"] = rng.choice(CITIES)
        row["region"] = rng.choice(REGIONS)
        row["status"] = rng.choice(STATUSES)

    elif template_name == "orders":
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        quantity = rng.randint(1, 20)
        unit_price = round(rng.uniform(5.0, 500.0), 2)
        total = round(quantity * unit_price, 2)
        row["order_id"] = str(5000 + row_idx)
        row["customer_name"] = f"{first} {last}"
        row["order_date"] = _random_date(rng)
        row["product"] = rng.choice(PRODUCTS)
        row["quantity"] = str(quantity)
        row["unit_price"] = f"{unit_price:.2f}"
        row["total"] = f"{total:.2f}"
        row["department"] = rng.choice(DEPARTMENTS)

    elif template_name == "products":
        row["product_id"] = str(2000 + row_idx)
        row["product_name"] = rng.choice(PRODUCTS)
        row["category"] = rng.choice(CATEGORIES)
        row["price"] = f"{round(rng.uniform(5.0, 999.99), 2):.2f}"
        row["in_stock"] = rng.choice(["true", "false"])
        row["rating"] = f"{round(rng.uniform(1.0, 5.0), 1):.1f}"
        row["release_date"] = _random_date(rng)
        row["status"] = rng.choice(STATUSES)

    return row


def _random_date(rng: random.Random) -> str:
    """Generate a random date in YYYY-MM-DD format."""
    year = rng.choice([2022, 2023, 2024, 2025])
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)  # safe for all months
    return f"{year}-{month:02d}-{day:02d}"


def _generate_clean_data(template_name: str, num_rows: int, rng: random.Random) -> List[Dict[str, str]]:
    """Generate a list of clean rows."""
    return [_generate_clean_row(template_name, i, rng) for i in range(num_rows)]


# ============================================================
# Error injectors
# ============================================================


def _inject_malformed_dates(rows: List[Dict[str, str]], types: Dict[str, str],
                            rng: random.Random, intensity: float) -> List[Dict[str, str]]:
    """Corrupt YYYY-MM-DD dates to various bad formats."""
    date_cols = [c for c, t in types.items() if t == "date_yyyy_mm_dd"]
    if not date_cols:
        return rows
    num_to_corrupt = max(1, int(len(rows) * intensity))
    indices = rng.sample(range(len(rows)), min(num_to_corrupt, len(rows)))
    bad_formats = [
        lambda d, r: f"{d[5:7]}/{d[8:10]}/{d[:4]}",          # MM/DD/YYYY
        lambda d, r: f"{d[8:10]}-{d[5:7]}-{d[:4]}",          # DD-MM-YYYY
        lambda d, r: f"{d[:4]}/{d[5:7]}/{d[8:10]}",          # YYYY/MM/DD
        lambda d, r: d.replace("-", ""),                       # YYYYMMDD
        lambda d, r: f"{_month_name(int(d[5:7]))} {int(d[8:10])} {d[:4]}",  # Month D YYYY
    ]
    for idx in indices:
        col = rng.choice(date_cols)
        original = rows[idx][col]
        if original and len(original) == 10 and original[4] == "-":
            fmt = rng.choice(bad_formats)
            rows[idx][col] = fmt(original, rng)
    return rows


def _month_name(m: int) -> str:
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    return months[m - 1]


def _inject_null_values(rows: List[Dict[str, str]], types: Dict[str, str],
                        rng: random.Random, intensity: float) -> List[Dict[str, str]]:
    """Replace random cells with empty strings."""
    cols = list(types.keys())
    num_nulls = max(1, int(len(rows) * len(cols) * intensity * 0.3))
    for _ in range(num_nulls):
        r = rng.randint(0, len(rows) - 1)
        c = rng.choice(cols)
        rows[r][c] = ""
    return rows


def _inject_duplicates(rows: List[Dict[str, str]], types: Dict[str, str],
                       rng: random.Random, intensity: float) -> List[Dict[str, str]]:
    """Insert duplicate rows at random positions."""
    num_dupes = max(1, int(len(rows) * intensity * 0.3))
    for _ in range(num_dupes):
        src = rng.randint(0, len(rows) - 1)
        pos = rng.randint(0, len(rows))
        rows.insert(pos, dict(rows[src]))
    return rows


def _inject_inconsistent_casing(rows: List[Dict[str, str]], types: Dict[str, str],
                                rng: random.Random, intensity: float) -> List[Dict[str, str]]:
    """Randomize casing on category columns."""
    cat_cols = [c for c, t in types.items() if t == "category"]
    if not cat_cols:
        return rows
    num_to_corrupt = max(1, int(len(rows) * intensity))
    indices = rng.sample(range(len(rows)), min(num_to_corrupt, len(rows)))
    for idx in indices:
        col = rng.choice(cat_cols)
        val = rows[idx][col]
        if val:
            transform = rng.choice([str.upper, str.lower, str.title, str.swapcase])
            rows[idx][col] = transform(val)
    return rows


def _inject_type_errors(rows: List[Dict[str, str]], types: Dict[str, str],
                        rng: random.Random, intensity: float) -> List[Dict[str, str]]:
    """Inject negative numbers and bad booleans."""
    int_cols = [c for c, t in types.items() if t == "integer"]
    float_cols = [c for c, t in types.items() if t == "float"]
    bool_cols = [c for c, t in types.items() if t == "boolean"]
    num_cols = int_cols + float_cols
    all_targets = num_cols + bool_cols
    if not all_targets:
        return rows
    num_to_corrupt = max(1, int(len(rows) * intensity * 0.5))
    indices = rng.sample(range(len(rows)), min(num_to_corrupt, len(rows)))
    for idx in indices:
        col = rng.choice(all_targets)
        if col in bool_cols:
            rows[idx][col] = rng.choice(["yes", "no", "1", "0", "TRUE", "FALSE", "Y", "N"])
        elif col in int_cols:
            val = rows[idx][col]
            try:
                n = int(val)
                rows[idx][col] = str(-abs(n) if n > 0 else n - rng.randint(1, 100))
            except (ValueError, TypeError):
                rows[idx][col] = str(-rng.randint(1, 999))
        elif col in float_cols:
            val = rows[idx][col]
            try:
                n = float(val)
                rows[idx][col] = f"{-abs(n):.2f}"
            except (ValueError, TypeError):
                rows[idx][col] = f"{-rng.uniform(1, 999):.2f}"
    return rows


def _inject_wrong_computed(rows: List[Dict[str, str]], types: Dict[str, str],
                           rng: random.Random, intensity: float) -> List[Dict[str, str]]:
    """Corrupt total = quantity * unit_price computations."""
    if "total" not in types or "quantity" not in types or "unit_price" not in types:
        return rows
    num_to_corrupt = max(1, int(len(rows) * intensity))
    indices = rng.sample(range(len(rows)), min(num_to_corrupt, len(rows)))
    for idx in indices:
        try:
            qty = float(rows[idx]["quantity"]) if rows[idx]["quantity"] else 1
            price = float(rows[idx]["unit_price"]) if rows[idx]["unit_price"] else 10.0
            correct = qty * price
            offset = rng.uniform(0.1, 0.5) * correct
            wrong = round(correct + rng.choice([-1, 1]) * offset, 2)
            rows[idx]["total"] = f"{wrong:.2f}"
        except (ValueError, TypeError):
            rows[idx]["total"] = f"{rng.uniform(1, 9999):.2f}"
    return rows


# ============================================================
# Registry and difficulty configuration
# ============================================================

ERROR_INJECTORS = {
    "malformed_dates": _inject_malformed_dates,
    "null_values": _inject_null_values,
    "duplicates": _inject_duplicates,
    "inconsistent_casing": _inject_inconsistent_casing,
    "type_errors": _inject_type_errors,
    "wrong_computed": _inject_wrong_computed,
}

DIFFICULTY_CONFIG = {
    "easy": {"num_error_types": 2, "intensity": 0.15},
    "medium": {"num_error_types": 4, "intensity": 0.25},
    "hard": {"num_error_types": 6, "intensity": 0.35},
}

# ============================================================
# Main generator
# ============================================================

_MAX_STEPS_MULTIPLIER = {
    "easy": 1.5,
    "medium": 2.0,
    "hard": 2.5,
}

_TEMPLATE_NAMES = list(COLUMN_TEMPLATES.keys())


def _rows_to_csv(columns: List[str], rows: List[Dict[str, str]]) -> str:
    """Convert rows to a CSV string."""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def generate_task(
    num_rows: int = 50,
    difficulty: str = "medium",
    seed: Optional[int] = None,
    error_types: Optional[List[str]] = None,
) -> Dict:
    """
    Generate a dirty-data cleaning task.

    Returns a dict with keys:
        dirty: CSV string with injected errors
        clean: CSV string of the ground truth
        types: dict mapping column names to types
        max_steps: maximum allowed agent steps
        difficulty: difficulty level used
        description: human-readable task description
    """
    if difficulty not in DIFFICULTY_CONFIG:
        raise ValueError(f"Unknown difficulty: {difficulty}. Must be one of {list(DIFFICULTY_CONFIG.keys())}")

    rng = random.Random(seed)
    config = DIFFICULTY_CONFIG[difficulty]

    # Pick a template
    template_name = rng.choice(_TEMPLATE_NAMES)
    tmpl = COLUMN_TEMPLATES[template_name]
    columns = tmpl["columns"]
    types = dict(tmpl["types"])

    # Generate clean data
    clean_rows = _generate_clean_data(template_name, num_rows, rng)

    # Deep copy for dirty data
    dirty_rows = [dict(r) for r in clean_rows]

    # Select error types
    if error_types is not None:
        selected_injectors = [(name, ERROR_INJECTORS[name]) for name in error_types if name in ERROR_INJECTORS]
    else:
        all_names = list(ERROR_INJECTORS.keys())
        rng.shuffle(all_names)
        n = config["num_error_types"]
        selected_injectors = [(name, ERROR_INJECTORS[name]) for name in all_names[:n]]

    intensity = config["intensity"]

    # Apply injectors
    applied_errors = []
    for name, injector in selected_injectors:
        dirty_rows = injector(dirty_rows, types, rng, intensity)
        applied_errors.append(name)

    # Build CSV strings
    clean_csv = _rows_to_csv(columns, clean_rows)
    dirty_csv = _rows_to_csv(columns, dirty_rows)

    # Compute max_steps
    multiplier = _MAX_STEPS_MULTIPLIER[difficulty]
    max_steps = int(num_rows * multiplier)

    # Build description
    error_desc = ", ".join(applied_errors) if applied_errors else "none"
    description = (
        f"Clean a {template_name} dataset with {num_rows} rows. "
        f"Difficulty: {difficulty}. "
        f"Error types injected: {error_desc}."
    )

    return {
        "dirty": dirty_csv,
        "clean": clean_csv,
        "types": types,
        "max_steps": max_steps,
        "difficulty": difficulty,
        "description": description,
    }
