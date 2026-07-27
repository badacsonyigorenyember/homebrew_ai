-- Semantic sanity: Irish Stout's nearest neighbours should be dark beers
WITH q AS (
  SELECT e.embedding FROM kb.chunk_embeddings e
  JOIN kb.chunks c ON c.id = e.chunk_id
  WHERE e.model='bge-m3' AND c.heading_path[3] LIKE '15B%'
  LIMIT 1
)
SELECT c.heading_path[3] AS style,
       round((e.embedding <=> (SELECT embedding FROM q))::numeric, 4) AS dist
FROM kb.chunk_embeddings e
JOIN kb.chunks c ON c.id = e.chunk_id
JOIN kb.document_versions v ON v.id = c.version_id AND v.is_current
WHERE e.model = 'bge-m3'
ORDER BY 2 LIMIT 8;