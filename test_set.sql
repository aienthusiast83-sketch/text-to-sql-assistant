SELECT DISTINCT COUNT(*) FROM TRACK;
SELECT SUM(GenreId) FROM TRACK;
SELECT * FROM TRACK;
SELECT * FROM GENRE;

SELECT SUM(total) FROM Invoice;
SELECT  * FROM InvoiceLine;
SELECT SUM(UnitPrice * Quantity) from  InvoiceLine;

select distinct Country, sum(a.total )
 from Invoice a, Customer b where a.CustomerId=b.CustomerId group by Country order by total DESC limit 5;
 
 SELECT c.Country, ROUND(SUM(i.Total), 2) AS Revenue
FROM Invoice i
JOIN Customer c ON i.CustomerId = c.CustomerId
GROUP BY c.Country
ORDER BY Revenue DESC
LIMIT 5;

-- Top 5 artists by revenue
-- Artist(ArtistId), InvoiceLine(TrackId), Track(TrackId), Album(ARTISTID),  

SELECT E.Name, SUM(A.UnitPrice*A.Quantity) as REV 
FROM InvoiceLine A 
JOIN TRACK C ON C.TrackId = A.TrackId
JOIN ALBUM D ON D.AlbumId= C.AlbumId
JOIN  Artist E ON D.ArtistId = E.ArtistId
GROUP BY E.ArtistId, E.Name ORDER BY REV DESC LIMIT 5;

-- Which album has the most tracks?
SELECT  TITLE,  AR.Name  , COUNT(T.TRACKID) TrackCount
FROM ALBUM A
JOIN TRACK T ON A.AlbumId=T.AlbumId
JOIN Artist ar ON A.ArtistId = ar.ArtistId
GROUP BY A.AlbumId, A.Title, AR.Name
ORDER BY TrackCount DESC LIMIT 1; 

-- 9. Revenue by year
select strftime('%Y', InvoiceDate) year, sum(total) from Invoice group by year;

-- 10. Average invoice amount per country
SELECT --DISTINCT COUNT(A.COUNTRY), 
 A.Country, 
ROUND(AVG(I.TOTAL), 2)  FROM Customer A
JOIN Invoice I ON I.CustomerId=A.CustomerId GROUP BY A.Country;




-- 11. Number of tracks per genre
SELECT COUNT(G.GenreId), 
count(G.Name) , t.Name--, T.TrackId, --G.Name GENRE_NAME, T.Name TRACK_NAME
FROM  Genre G
JOIN Track T ON T.GenreId=G.GenreId GROUP BY G.GenreId order by COUNT(G.GenreId) desc ;



-- Q12: which sales rep generated the most revenue?
SELECT CONCAT(E.FirstName,' ', E.LastName) SALESREP, SUM(I.total) REV
FROM Customer C
JOIN Invoice I ON I.CustomerId=C.CustomerId
JOIN Employee E ON E.EmployeeId=C.SupportRepId GROUP BY E.EmployeeId, SALESREP ORDER BY REV DESC LIMIT 1;



-- Q13: customers who spent more than $45 in total.
SELECT C.FirstName|| ' ' || C.LastName Cust_Name, Sum(i.total ) Total
FROM Customer C
JOIN Invoice I ON I.CustomerId=C.CustomerId 
GROUP by c.CustomerId, Cust_Name HAVING sum(i.total) > 45 ORDER by Total DESC ;



-- 14. Longest track, in minutes
SELECT  Milliseconds, ROund(T.Milliseconds/60000.0, 2) Minutes, t.Name Track_Name
FROM Track T  order by Minutes DESC limit 1;

-- To Cross Verify manually
select* from Track where name='Occupation / Precipice';


-- Q15: top genre in each country by revenue
SELECT *FROM Invoice I; -- BillingCountry, CustomerId
SELECT  DISTINCT BillingCountry, sum(total), * FROM Invoice I group by BillingCountry order by sum(total)  desc; -- BillingCountry, CustomerId
SELECT * FROM Genre; -- GenreId, Name
select *from InvoiceLine; -- InvoiceId, TrackId
select *from Customer; -- CustomerId, Country
select *from Track; -- TrackId, GenreId, AlbumId, Track=_Name

SELECT  I.BillingCountry country, G.Name Genre_Name,
--C.Country, C.FirstName||' '||C.LastName Cust_Name, 
SUM(IL.UnitPrice*IL.Quantity) Rev
--sum(I.Total) Rev
FROM Track T--Customer C
JOIN Genre G ON G.GenreId=T.GenreId
JOIN Invoice I ON I.InvoiceId=IL.InvoiceId
JOIN InvoiceLine IL ON IL.TrackId=T.TrackId GROUP BY  I.BillingCountry, G.NAME ORDER BY I.BillingCountry DESC ;


WITH genre_revenue_ranked AS (
    SELECT 
        c.Country,
        g.Name AS genre_name,
        SUM(il.UnitPrice * il.Quantity) AS total_revenue,
        RANK() OVER (
            PARTITION BY c.Country 
            ORDER BY SUM(il.UnitPrice * il.Quantity) DESC
        ) AS rank_num
    FROM Customer c
    JOIN invoice i ON c.CustomerId = i.CustomerId
    JOIN invoiceline il ON i.InvoiceId = il.InvoiceId
    JOIN Track t ON il.TrackId = t.TrackId
    JOIN Genre g ON t.GenreId = g.GenreId
    GROUP BY c.Country, g.Name
)
SELECT 
    Country,
    genre_name,
    ROUND(total_revenue, 2) AS revenue
FROM genre_revenue_ranked
WHERE rank_num = 1
ORDER BY Country ASC;


-- 16. Month-over-month revenue change in the latest year

WITH MonthlyRevenue AS (
    SELECT 
        strftime('%Y-%m', InvoiceDate) AS sales_month, -- Truncates to YYYY-MM-01
        SUM(total) AS current_month_revenue
    FROM Invoice
    WHERE strftime('%Y', InvoiceDate) = (SELECT MAX(strftime('%Y', InvoiceDate)) FROM Invoice)
    GROUP BY strftime('%Y-%m', InvoiceDate)
),
MoMCalculation AS (
    SELECT 
        sales_month,
        current_month_revenue,
        LAG(current_month_revenue, 1) OVER (ORDER BY sales_month) AS previous_month_revenue
    FROM MonthlyRevenue
)
SELECT 
   -- STRFTIME('%Y-%m', sales_month) AS 
	sales_month, -- Formats date to YYYY-MM
    ROUND(current_month_revenue, 2) AS current_revenue,
    ROUND(previous_month_revenue, 2) AS previous_revenue,
    -- Calculate absolute difference
    ROUND(current_month_revenue - previous_month_revenue, 2) AS absolute_change,
    -- Calculate percentage difference (safeguarded against division by zero)
    ROUND(
        100.0 * (current_month_revenue - previous_month_revenue) / 
        NULLIF(previous_month_revenue, 0), 
        2
    ) AS mom_growth_pct
FROM MoMCalculation
ORDER BY sales_month;




-- 17. Customers who never bought a Rock track
SELECT *FROM Customer; -- EmployeeId
SELECT* FROM Genre where Name='Rock';
SELECT *FROM Track; -- AlbumId, GenreId
SELECT distinct G.*, t.Name Track_Name, T.AlbumId
 FROM Genre G 
JOIN TRACK T ON T.TrackId=T.TrackId
where G.Name='Rock';
select DIstinct --G.name,  
c.FirstName||' '|| C.LastName Cust_Name 
from Invoice I
Join  InvoiceLine IL on I.InvoiceId=IL.InvoiceId
Join Customer C on c.CustomerId= I.CustomerId
Join Track T on IL.TrackId = T.TrackId 
Join Genre G on G.GenreId=t.GenreId WHERE g.Name  !=  'Rock' order by Cust_Name ;

SELECT
    C.FirstName || ' ' || C.LastName AS Cust_Name
FROM Customer C
WHERE NOT EXISTS (
    SELECT 1
    FROM Invoice I
    JOIN InvoiceLine IL ON IL.InvoiceId = I.InvoiceId
    JOIN Track T        ON T.TrackId    = IL.TrackId
    JOIN Genre G        ON G.GenreId    = T.GenreId
    WHERE I.CustomerId = C.CustomerId
      AND G.Name = 'Rock'
)
ORDER BY Cust_Name;

SELECT COUNT(DISTINCT I.CustomerId)
FROM Invoice I
JOIN InvoiceLine IL ON IL.InvoiceId = I.InvoiceId
JOIN Track T        ON T.TrackId    = IL.TrackId
JOIN Genre G        ON G.GenreId    = T.GenreId
WHERE G.Name <> 'Rock';



-- Q18: each sales rep’s percentage share of total revenue.
select *from Employee;
SELECT CONCAT(E.FirstName,' ', E.LastName) SALESREP,  
	SUM(I.total) Tot_Rev,
--    SUM(total) OVER() AS Rev_Per,
	ROUND((SUM(I.total)*100.0/sum(sum(i.total)) over ()), 2)  Rev_Perc
FROM Customer C
JOIN Invoice I ON I.CustomerId=C.CustomerId
JOIN Employee E ON E.EmployeeId=C.SupportRepId GROUP BY E.EmployeeId, 
SALESREP ORDER BY Tot_Rev DESC;


SELECT
    E.FirstName || ' ' || E.LastName AS SalesRep,
    ROUND(SUM(I.Total), 2) AS Tot_Rev,
    ROUND(SUM(I.Total) * 100.0 / SUM(SUM(I.Total)) OVER (), 2) AS Rev_Perc
FROM Customer C
JOIN Invoice  I ON I.CustomerId = C.CustomerId
JOIN Employee E ON E.EmployeeId = C.SupportRepId
GROUP BY E.EmployeeId, SalesRep
ORDER BY Tot_Rev DESC;



-- Q19: customers who made a purchase in every year.
SELECT *FROM CUSTOMER;
SELECT DISTINCT count( strftime('%Y', InvoiceDate)) Year1,  C.FirstName||' '||C.LastName Cust_name, strftime('%Y', InvoiceDate) Year FROM Invoice I
JOIN CUSTOMER C ON C.CustomerId=I.CustomerId 
where Year = '2009'
 group by Year, Cust_Name order by Year, Cust_Name Desc;
 
 
SELECT c.CustomerId, C.FirstName||' ' ||c.LastName Cust_Name,  Count(distinct strftime('%Y', InvoiceDate) ) Year
FROM invoice I join Customer C on i.CustomerId=c.CustomerId
GROUP BY I.CustomerId
HAVING COUNT(DISTINCT strftime('%Y', InvoiceDate)) = (
    SELECT COUNT(DISTINCT strftime('%Y', InvoiceDate)) 
    FROM Invoice)
	Order by Cust_Name;
	
	SELECT
    C.CustomerId,
    C.FirstName || ' ' || C.LastName AS Cust_Name,
    COUNT(DISTINCT strftime('%Y', I.InvoiceDate)) AS Years_Active
FROM Invoice I
JOIN Customer C ON I.CustomerId = C.CustomerId
GROUP BY C.CustomerId, Cust_Name
HAVING COUNT(DISTINCT strftime('%Y', I.InvoiceDate)) = (
    SELECT COUNT(DISTINCT strftime('%Y', InvoiceDate))
    FROM Invoice
)
ORDER BY Cust_Name;




-- Q20: “Who are our best customers?”
SELECT *FROM Customer;
SELECT *FROM Invoice;
select c.FirstName|| ' ' || c.LastName Cust_Name, Sum(total) Rev from Customer c
join invoice i on i.CustomerId=c.CustomerId group by c.CustomerId, cust_name order by Rev DESC ;

SELECT C.CustomerId,
           C.FirstName || ' ' || C.LastName AS Cust_Name,
           MAX(I.InvoiceDate) AS LastPurchase,
           COUNT(I.InvoiceId) AS Frequency,
           ROUND(SUM(I.Total), 2) AS Monetary
    FROM Customer C
    JOIN Invoice I ON I.CustomerId = C.CustomerId
    GROUP BY C.CustomerId, Cust_Name
