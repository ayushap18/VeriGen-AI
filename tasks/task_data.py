"""
Task definitions for the Data Cleaning Environment.
Each task has: dirty data, clean (ground truth) data, column types, and a grader.
"""

import csv
import io
from typing import Any


# ============================================================
# TASK 1 (EASY): Fix dates and handle missing values
# ============================================================

TASK1_DIRTY = """name,email,signup_date,age,city
Alice Johnson,alice@example.com,2024-01-15,28,New York
Bob Smith,bob@example.com,01/20/2024,35,Los Angeles
Charlie Brown,,2024-02-10,,Chicago
Diana Ross,diana@example.com,March 5 2024,42,Houston
Eve Davis,eve@example.com,2024-03-15,29,Phoenix
Frank Miller,frank@example.com,2024/04/01,31,
Grace Lee,grace@example.com,15-05-2024,,Dallas
Henry Wilson,henry@example.com,2024-06-20,45,San Jose"""

TASK1_CLEAN = """name,email,signup_date,age,city
Alice Johnson,alice@example.com,2024-01-15,28,New York
Bob Smith,bob@example.com,2024-01-20,35,Los Angeles
Charlie Brown,unknown@example.com,2024-02-10,0,Chicago
Diana Ross,diana@example.com,2024-03-05,42,Houston
Eve Davis,eve@example.com,2024-03-15,29,Phoenix
Frank Miller,frank@example.com,2024-04-01,31,Unknown
Grace Lee,grace@example.com,2024-05-15,0,Dallas
Henry Wilson,henry@example.com,2024-06-20,45,San Jose"""

TASK1_TYPES = {
    "name": "string",
    "email": "string",
    "signup_date": "date_yyyy_mm_dd",
    "age": "integer",
    "city": "string"
}


# ============================================================
# TASK 2 (MEDIUM): Deduplicate and normalize categories
# ============================================================

TASK2_DIRTY = """product_id,product_name,category,price,in_stock
101,Wireless Mouse,Electronics,29.99,true
102,USB Keyboard,electronics,49.99,true
103,Wireless Mouse,Electronics,29.99,true
104,Desk Lamp,Home & Office,34.99,yes
105,Monitor Stand,home & office,45.00,true
106,Webcam HD,ELECTRONICS,79.99,false
107,Desk Lamp,Home and Office,34.99,true
108,Notebook A5,Stationery,5.99,true
109,Pen Set,stationery,12.99,TRUE
110,Webcam HD,Electronics,79.99,false
111,Eraser Pack,STATIONERY,2.99,true
112,Mouse Pad,Electronics,15.99,true"""

TASK2_CLEAN = """product_id,product_name,category,price,in_stock
101,Wireless Mouse,Electronics,29.99,true
102,USB Keyboard,Electronics,49.99,true
104,Desk Lamp,Home & Office,34.99,true
105,Monitor Stand,Home & Office,45.00,true
106,Webcam HD,Electronics,79.99,false
108,Notebook A5,Stationery,5.99,true
109,Pen Set,Stationery,12.99,true
111,Eraser Pack,Stationery,2.99,true
112,Mouse Pad,Electronics,15.99,true"""

TASK2_TYPES = {
    "product_id": "integer",
    "product_name": "string",
    "category": "category",
    "price": "float",
    "in_stock": "boolean"
}


# ============================================================
# TASK 3 (HARD): Full pipeline cleaning
# ============================================================

TASK3_DIRTY = """order_id,customer_name,order_date,product,quantity,unit_price,total,status,region
1001,John Doe,2024-01-10,Widget A,5,10.00,50.00,Shipped,North
1002,Jane Smith,01/15/2024,Widget B,3,20.00,60.00,shipped,South
1003,John Doe,2024-01-10,Widget A,5,10.00,50.00,Shipped,North
1004,Bob Lee,,Widget C,-2,15.00,-30.00,Pending,East
1005,Alice Wong,2024-02-01,Widget A,10,10.00,100.00,DELIVERED,West
1006,Charlie Day,Feb 5 2024,Widget D,1,999999.99,999999.99,Shipped,north
1007,Jane Smith,2024-02-10,Widget B,0,20.00,0.00,Cancelled,South
1008,,2024-02-15,Widget E,4,25.00,100.00,Pending,East
1009,Eve Black,2024-03-01,Widget A,2,10.00,25.00,Delivered,West
1010,Frank White,2024/03/05,Widget F,3,30.00,90.00,shipped,South
1011,Grace Hall,2024-03-10,Widget B,1,20.00,20.00,Delivered,
1012,Bob Lee,2024-01-05,Widget C,2,15.00,30.00,Pending,East"""

TASK3_CLEAN = """order_id,customer_name,order_date,product,quantity,unit_price,total,status,region
1001,John Doe,2024-01-10,Widget A,5,10.00,50.00,Shipped,North
1002,Jane Smith,2024-01-15,Widget B,3,20.00,60.00,Shipped,South
1004,Bob Lee,2024-01-05,Widget C,2,15.00,30.00,Pending,East
1005,Alice Wong,2024-02-01,Widget A,10,10.00,100.00,Delivered,West
1006,Charlie Day,2024-02-05,Widget D,1,50.00,50.00,Shipped,North
1007,Jane Smith,2024-02-10,Widget B,0,20.00,0.00,Cancelled,South
1008,Unknown,2024-02-15,Widget E,4,25.00,100.00,Pending,East
1009,Eve Black,2024-03-01,Widget A,2,10.00,20.00,Delivered,West
1010,Frank White,2024-03-05,Widget F,3,30.00,90.00,Shipped,South
1011,Grace Hall,2024-03-10,Widget B,1,20.00,20.00,Delivered,Unknown"""

TASK3_TYPES = {
    "order_id": "integer",
    "customer_name": "string",
    "order_date": "date_yyyy_mm_dd",
    "product": "string",
    "quantity": "integer",
    "unit_price": "float",
    "total": "float",
    "status": "category",
    "region": "category"
}


# ============================================================
# Task registry
# ============================================================

TASKS = {
    "fix_dates_and_nulls": {
        "dirty": TASK1_DIRTY.strip(),
        "clean": TASK1_CLEAN.strip(),
        "types": TASK1_TYPES,
        "max_steps": 20,
        "difficulty": "easy",
        "description": "Fix malformed date formats and handle missing values in a customer dataset."
    },
    "dedup_and_normalize": {
        "dirty": TASK2_DIRTY.strip(),
        "clean": TASK2_CLEAN.strip(),
        "types": TASK2_TYPES,
        "max_steps": 25,
        "difficulty": "medium",
        "description": "Remove duplicate rows and normalize inconsistent category names in a product dataset."
    },
    "full_pipeline_clean": {
        "dirty": TASK3_DIRTY.strip(),
        "clean": TASK3_CLEAN.strip(),
        "types": TASK3_TYPES,
        "max_steps": 40,
        "difficulty": "hard",
        "description": "Full end-to-end cleaning: fix types, dates, duplicates, missing values, outliers, and computed fields."
    }
}


def parse_csv(csv_string: str) -> list[dict[str, str]]:
    """Parse CSV string into list of dicts."""
    reader = csv.DictReader(io.StringIO(csv_string.strip()))
    return [row for row in reader]


def rows_to_csv(rows: list[dict[str, str]], columns: list[str]) -> str:
    """Convert list of dicts back to CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue().strip()


def grade(current_csv: str, clean_csv: str) -> float:
    """
    Grade the current dataset against the ground truth.
    Returns a score between 0.0 and 1.0.
    
    Scoring:
    - 40% row match (correct number of rows, correct row content)
    - 40% cell-level accuracy (each cell compared individually)
    - 20% structural match (correct columns, correct order)
    """
    try:
        current_rows = parse_csv(current_csv)
        clean_rows = parse_csv(clean_csv)
    except Exception:
        return 0.0

    if not clean_rows:
        return 0.0

    clean_columns = list(clean_rows[0].keys())
    current_columns = list(current_rows[0].keys()) if current_rows else []

    # Structural score (20%): do columns match?
    if current_columns == clean_columns:
        structural_score = 1.0
    elif set(current_columns) == set(clean_columns):
        structural_score = 0.5
    else:
        structural_score = 0.0

    # Row match score (40%): how many rows match exactly?
    clean_row_strs = [str(sorted(row.items())) for row in clean_rows]
    current_row_strs = [str(sorted(row.items())) for row in current_rows]

    matched = sum(1 for r in current_row_strs if r in clean_row_strs)
    row_precision = matched / len(current_row_strs) if current_row_strs else 0
    row_recall = matched / len(clean_row_strs) if clean_row_strs else 0
    row_score = (2 * row_precision * row_recall / (row_precision + row_recall)) if (row_precision + row_recall) > 0 else 0.0

    # Cell accuracy score (40%): cell-by-cell comparison
    total_cells = 0
    correct_cells = 0
    for i, clean_row in enumerate(clean_rows):
        if i < len(current_rows):
            for col in clean_columns:
                total_cells += 1
                clean_val = clean_row.get(col, "").strip().lower()
                current_val = current_rows[i].get(col, "").strip().lower()
                if clean_val == current_val:
                    correct_cells += 1
        else:
            total_cells += len(clean_columns)

    cell_score = correct_cells / total_cells if total_cells > 0 else 0.0

    final_score = (0.2 * structural_score) + (0.4 * row_score) + (0.4 * cell_score)
    return round(min(max(final_score, 0.0), 1.0), 4)
