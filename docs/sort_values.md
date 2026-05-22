# Sorting Query Results with `sort_values`

`sqlframe` exposes a pandas-style `sort_values` method on frame objects via the
`OrderByMixin`.  Under the hood it generates a `SELECT * FROM … ORDER BY …`
statement that is executed lazily when you call `.to_pandas()`.

## Basic Usage

```python
import sqlframe

conn = sqlframe.Connection.from_url("postgresql://user:pass@localhost/mydb")
df = sqlframe.read_table(conn, "sales")

# Sort by a single column ascending (default)
result = df.sort_values("amount").to_pandas()

# Sort descending
result = df.sort_values("amount", ascending=False).to_pandas()
```

## Multi-Column Sort

Pass a list of column names and a matching list of booleans:

```python
result = df.sort_values(
    by=["region", "amount"],
    ascending=[True, False],   # region ASC, amount DESC
).to_pandas()
```

## Chaining with `where` and `limit`

`OrderByFrame` supports `.where()` and `.limit()` for further refinement:

```python
result = (
    df.sort_values("created_at", ascending=False)
      .where("status = 'active'")
      .limit(100)
      .to_pandas()
)
```

The generated SQL will look like:

```sql
SELECT * FROM sales
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 100
```

## API Reference

### `OrderByMixin.sort_values(by, ascending=True)`

| Parameter   | Type                     | Description                                      |
|-------------|--------------------------|--------------------------------------------------|
| `by`        | `str \| list[str]`       | Column(s) to sort by.                            |
| `ascending` | `bool \| list[bool]`     | Sort direction(s). Defaults to `True` (ASC).     |

Returns an `OrderByFrame` instance.

### `OrderByFrame.limit(n)`

Returns a new `OrderByFrame` with `LIMIT n` appended.

### `OrderByFrame.where(condition, **params)`

Returns a new `OrderByFrame` with a `WHERE` clause.

### `OrderByFrame.to_pandas()`

Executes the query and returns a `pandas.DataFrame`.
