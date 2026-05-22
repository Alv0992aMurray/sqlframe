# Column Casting

SqlFrame lets you cast one or more columns to a different SQL type before
pulling results into a Pandas DataFrame.

## Quick start

```python
import sqlframe

conn = sqlframe.Connection.from_url("postgresql://user:pass@localhost/mydb")

df = (
    sqlframe.read_table(conn, "orders")
    .select("id", "amount", "created_at")
    .cast({"amount": "numeric", "created_at": "date"})
    .to_pandas()
)
```

This generates:

```sql
SELECT id,
       CAST(amount AS NUMERIC) AS amount,
       CAST(created_at AS DATE) AS created_at
FROM orders
```

## Supported type aliases

| Alias | SQL type |
|-------|----------|
| `int` / `integer` | `INTEGER` |
| `float` | `FLOAT` |
| `double` | `DOUBLE PRECISION` |
| `str` / `string` | `VARCHAR` |
| `text` | `TEXT` |
| `bool` / `boolean` | `BOOLEAN` |
| `date` | `DATE` |
| `datetime` / `timestamp` | `TIMESTAMP` |
| `numeric` | `NUMERIC` |
| `decimal` | `DECIMAL` |

Any other value is passed through verbatim (upper-cased), so database-specific
types like `JSONB` or `UUID` work too.

## Chaining with other operations

```python
(
    sqlframe.read_table(conn, "events")
    .select("user_id", "score", "event_date")
    .where("score IS NOT NULL")
    .cast({"score": "float", "event_date": "date"})
    .limit(1000)
    .to_pandas()
)
```

## Validation

`cast()` raises a `ValueError` if:

- You have not yet called `.select()` with explicit column names (i.e. the
  current column list is `["*"]`).
- A column name passed to `cast()` does not appear in the current selection.

```python
# This raises ValueError – no explicit columns selected
sqlframe.read_table(conn, "orders").cast({"amount": "float"})

# This raises ValueError – 'price' is not in the selection
sqlframe.read_table(conn, "orders").select("id", "amount").cast({"price": "float"})
```
