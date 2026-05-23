# Top-N Queries

The `top_n` and `bottom_n` helpers let you retrieve the highest or lowest *n*
rows from a table with a single, readable call — no need to write `ORDER BY`
or `LIMIT` by hand.

## Quick start

```python
import sqlframe

conn = sqlframe.connect("postgresql://user:pass@localhost/mydb")
df = sqlframe.read_table(conn, "orders")

# 10 most-expensive orders
top_orders = df.top_n(10, order_by="total_amount")
print(top_orders)          # TopNFrame — lazy, no query yet
result = top_orders.to_pandas()   # executes SQL, returns DataFrame
```

## API reference

### `frame.top_n(n, order_by, columns=None)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `n` | `int` | Number of rows to return. |
| `order_by` | `str \| list[str]` | Column(s) to sort **ascending**. |
| `columns` | `str \| list[str] \| None` | Columns to `SELECT`. `None` → `*`. |

Returns a **`TopNFrame`** (lazy).

### `frame.bottom_n(n, order_by, columns=None)`

Same as `top_n` but sorts **descending** — useful for finding the smallest
values.

## Chaining `.where()`

`TopNFrame` supports `.where()` for additional filtering:

```python
(
    df.top_n(5, order_by="score", columns=["user_id", "score"])
      .where("region = 'EU'")
      .to_pandas()
)
```

Generated SQL:

```sql
SELECT user_id, score
FROM   users
WHERE  region = 'EU'
ORDER  BY score ASC
LIMIT  5
```

## Multiple sort columns

```python
df.top_n(20, order_by=["department", "salary"]).to_pandas()
```

```sql
SELECT * FROM employees
ORDER BY department ASC, salary ASC
LIMIT 20
```

## Notes

- `top_n` / `bottom_n` inherit any `WHERE` clause already present on the
  parent frame, so pre-filtering with `.where()` on a `SqlFrame` is fully
  composable.
- The resulting `TopNFrame` is **lazy**: no query is sent until `.to_pandas()`
  is called.
