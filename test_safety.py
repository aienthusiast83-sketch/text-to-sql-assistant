from text_to_sql import is_safe, run_sql

tests = [
    "SELECT COUNT(*) FROM Customer",
    "WITH x AS (SELECT 1) SELECT * FROM x",
    "DELETE FROM Customer",
    "DROP TABLE Customer",
    "UPDATE Customer SET FirstName = 'X'",
    "SELECT 1; DROP TABLE Customer",
]

print("Layer 1: is_safe()")
for sql in tests:
    ok, reason = is_safe(sql)
    print(f"  {'ALLOWED' if ok else 'BLOCKED':8} | {sql}  {reason}")

print("\nLayer 2: read-only database (bypassing is_safe on purpose)")
try:
    run_sql("DELETE FROM Customer")
    print("  FAILED: the delete ran!")
except Exception as e:
    print(f"  PASSED: {e}")