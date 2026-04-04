# DB Session Lifetime in Streaming Endpoints

**Tags:** `database` `sqlalchemy` `streaming` `performance`

## Concept
Do DB reads first, close DB session, then start long-lived stream.

## When to use
- Streaming endpoint has metadata lookup before stream

## When NOT to use
- Endpoint requires active DB transaction during response

## Minimal pattern
```py
async with AsyncSessionLocal() as db:
    movie = await db.scalar(select(Movie).where(Movie.id == movie_id))
# DB session closed here
return StreamingResponse(iterfile(movie))
```
