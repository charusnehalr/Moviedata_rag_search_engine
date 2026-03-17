f"""Rank the movies listed below by relevance to the following search query.

Query: "{query}"

Movies:
{doc_list_str}

Return ONLY the movie IDs in order of relevance (best match first).You MUST return exactly {num_docs} IDs. Return a valid JSON list, nothing else. 

For example:
[75, 12, 34, 2, 1]

This means the movie with idx of 75 is most relevant. 

I will be parsing with json.loads, so nothing but the list.

Results: 