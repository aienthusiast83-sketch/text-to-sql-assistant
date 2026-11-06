TEST_CASES = [
    {"id": 1, "grade": True, "question": "How many customers are there?",
     "expected_sql": "SELECT COUNT(*) AS n FROM Customer"},

    {"id": 2, "grade": True, "question": "Which countries do customers come from?",
     "expected_sql": "SELECT DISTINCT Country FROM Customer"},

    {"id": 3, "grade": True, "question": "How many tracks are in the database?",
     "expected_sql": "SELECT COUNT(*) AS n FROM Track"},

    {"id": 4, "grade": True, "question": "List all genres.",
     "expected_sql": "SELECT Name FROM Genre"},

    {"id": 5, "grade": True, "question": "What is the total sales revenue?",
     "expected_sql": "SELECT SUM(Total) AS Revenue FROM Invoice"},

    {"id": 6, "grade": True, "question": "Top 5 countries by revenue",
     "expected_sql": """
        SELECT BillingCountry, SUM(Total) AS Revenue
        FROM Invoice GROUP BY BillingCountry
        ORDER BY Revenue DESC LIMIT 5"""},

    {"id": 7, "grade": True, "question": "Top 5 artists by revenue",
     "expected_sql": """
        SELECT ar.Name, SUM(il.UnitPrice * il.Quantity) AS Revenue
        FROM InvoiceLine il
        JOIN Track t ON t.TrackId = il.TrackId
        JOIN Album al ON al.AlbumId = t.AlbumId
        JOIN Artist ar ON ar.ArtistId = al.ArtistId
        GROUP BY ar.ArtistId ORDER BY Revenue DESC LIMIT 5"""},

    {"id": 8, "grade": True, "question": "Which album has the most tracks?",
     "expected_sql": """
        SELECT al.Title, COUNT(*) AS Tracks
        FROM Album al JOIN Track t ON t.AlbumId = al.AlbumId
        GROUP BY al.AlbumId ORDER BY Tracks DESC LIMIT 1"""},

    {"id": 9, "grade": True, "question": "Revenue by year",
     "expected_sql": """
        SELECT strftime('%Y', InvoiceDate) AS Year, SUM(Total) AS Revenue
        FROM Invoice GROUP BY Year ORDER BY Year"""},

    {"id": 10, "grade": True, "question": "Average invoice amount per country",
     "expected_sql": """
        SELECT BillingCountry, AVG(Total) AS AvgInvoice
        FROM Invoice GROUP BY BillingCountry"""},

    {"id": 11, "grade": True, "question": "Number of tracks per genre",
     "expected_sql": """
        SELECT g.Name, COUNT(*) AS Tracks
        FROM Genre g JOIN Track t ON t.GenreId = g.GenreId
        GROUP BY g.GenreId"""},

    {"id": 12, "grade": True, "question": "Which sales rep generated the most revenue?",
     "expected_sql": """
        SELECT e.FirstName || ' ' || e.LastName AS Rep, SUM(i.Total) AS Revenue
        FROM Employee e
        JOIN Customer c ON c.SupportRepId = e.EmployeeId
        JOIN Invoice i ON i.CustomerId = c.CustomerId
        GROUP BY e.EmployeeId ORDER BY Revenue DESC LIMIT 1"""},

    {"id": 13, "grade": True, "question": "Customers who spent more than $45 in total",
     "expected_sql": """
        SELECT c.FirstName || ' ' || c.LastName AS Customer, SUM(i.Total) AS Total
        FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId
        GROUP BY c.CustomerId HAVING SUM(i.Total) > 45"""},

    {"id": 14, "grade": True, "question": "Longest track, in minutes",
     "expected_sql": """
        SELECT Name, Milliseconds / 60000.0 AS Minutes
        FROM Track ORDER BY Milliseconds DESC LIMIT 1"""},

    {"id": 15, "grade": True, "question": "Top genre in each country by revenue",
     "expected_sql": """
        WITH cg AS (
            SELECT i.BillingCountry AS Country, g.Name AS Genre,
                   SUM(il.UnitPrice * il.Quantity) AS Revenue,
                   RANK() OVER (PARTITION BY i.BillingCountry
                                ORDER BY SUM(il.UnitPrice * il.Quantity) DESC) AS rnk
            FROM InvoiceLine il
            JOIN Invoice i ON i.InvoiceId = il.InvoiceId
            JOIN Track t ON t.TrackId = il.TrackId
            JOIN Genre g ON g.GenreId = t.GenreId
            GROUP BY i.BillingCountry, g.GenreId)
        SELECT Country, Genre, Revenue FROM cg WHERE rnk = 1"""},

    {"id": 16, "grade": True, "question": "Month-over-month revenue change in the latest year",
     # Compare every month with the previous month first, then keep the latest year,
     # so January is compared with December of the year before.
     "expected_sql": """
        WITH m AS (
            SELECT strftime('%Y-%m', InvoiceDate) AS Month, SUM(Total) AS Revenue
            FROM Invoice GROUP BY Month),
        c AS (
            SELECT Month, Revenue - LAG(Revenue) OVER (ORDER BY Month) AS Change FROM m)
        SELECT Month, Change FROM c
        WHERE substr(Month, 1, 4) =
              (SELECT MAX(strftime('%Y', InvoiceDate)) FROM Invoice)
        ORDER BY Month"""},

    {"id": 17, "grade": True, "question": "Customers who never bought a Rock track",
     "expected_sql": """
        SELECT c.FirstName || ' ' || c.LastName AS Customer
        FROM Customer c
        WHERE NOT EXISTS (
            SELECT 1 FROM Invoice i
            JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
            JOIN Track t ON t.TrackId = il.TrackId
            JOIN Genre g ON g.GenreId = t.GenreId
            WHERE i.CustomerId = c.CustomerId AND g.Name = 'Rock')"""},

    {"id": 18, "grade": True, "question": "Each sales rep's percentage share of total revenue",
     "expected_sql": """
        SELECT e.FirstName || ' ' || e.LastName AS Rep,
               SUM(i.Total) * 100.0 / (SELECT SUM(Total) FROM Invoice) AS SharePct
        FROM Employee e
        JOIN Customer c ON c.SupportRepId = e.EmployeeId
        JOIN Invoice i ON i.CustomerId = c.CustomerId
        GROUP BY e.EmployeeId"""},

    {"id": 19, "grade": True, "question": "Customers who made a purchase in every year",
     "expected_sql": """
        SELECT c.FirstName || ' ' || c.LastName AS Customer
        FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId
        GROUP BY c.CustomerId
        HAVING COUNT(DISTINCT strftime('%Y', i.InvoiceDate)) =
               (SELECT COUNT(DISTINCT strftime('%Y', InvoiceDate)) FROM Invoice)"""},

    {"id": 20, "grade": False, "question": "Who are our best customers?",
     "expected_sql": """
        SELECT c.FirstName || ' ' || c.LastName AS Customer, SUM(i.Total) AS Spend
        FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId
        GROUP BY c.CustomerId ORDER BY Spend DESC LIMIT 5"""},
]