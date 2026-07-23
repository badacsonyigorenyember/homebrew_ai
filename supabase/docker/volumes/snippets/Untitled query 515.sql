-- 1. Delete all rows after the 117th row
WITH ordered_rows AS (
    SELECT ctid, ROW_NUMBER() OVER (ORDER BY id ASC) AS row_num
    FROM documents
)
DELETE FROM documents
WHERE ctid IN (
    SELECT ctid 
    FROM ordered_rows 
    WHERE row_num > 117
);

-- 2. Dynamically reset the id sequence to resume at 118
SELECT setval(pg_get_serial_sequence('documents', 'id'), 117);
