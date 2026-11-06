from evaluate import run_expected, results_match, candidate_columns, column_values
from test_cases import TEST_CASES

ai_sql = """
SELECT c.CustomerId, c.FirstName, c.LastName
FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId, c.FirstName, c.LastName
HAVING COUNT(DISTINCT strftime('%Y', i.InvoiceDate)) =
       (SELECT COUNT(DISTINCT strftime('%Y', InvoiceDate)) FROM Invoice)
"""

expected = run_expected(TEST_CASES[18]["expected_sql"])   # Q19
actual = run_expected(ai_sql)

print("AI column types:\n", actual.dtypes, "\n")
print("Expected (first 3):", column_values(expected["Customer"])[:3])
for col in candidate_columns(actual):
    print("Candidate (first 3):", col[:3])
print("\nMATCH:", results_match(expected, actual))