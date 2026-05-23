# Between Filter

The `.between()` method lets you filter rows where a column's value falls
within a closed numeric (or date) range — translated directly to a SQL
`BETWEEN` clause for efficient server-side filtering.

## Basic usage

```python
import sqlframe

conn = sqlframe.connect("postgresql://user:pass@localhost/mydb")
df = sqlframe.read_table(conn, "orders")

# Fetch orders where amount is between 100 and 500
result = df.between("amount", 100, 500).to_pandas()
print(result.head())
```

Generated SQL:

```sql
SELECT * FROM orders WHERE amount BETWEEN ? AND ?
-- params: [100, 500]
```

## Projecting specific columns

```python
result = df.between("amount", 100, 500, columns=["id", "customer", "amount"]).to_pandas()
```

```sql
SELECT id, customer, amount FROM orders WHERE amount BETWEEN ? AND ?
```

## Chaining additional filters

```python
result = (
    df.between("amount", 100, 500)
      .where("status = 'completed'")
      .limit(50)
      .to_pandas()
)
```

```sql
SELECT * FROM orders
WHERE amount BETWEEN ? AND ?
  AND (status = 'completed')
LIMIT 50
```

## Date ranges

`BETWEEN` works equally well with date strings:

```python
result = df.between("order_date", "2024-01-01", "2024-03-31").to_pandas()
```

## API reference

### `SqlFrame.between(column, low, high, columns=None)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `column` | `str` | Column name to filter on |
| `low` | `Any` | Lower bound (inclusive) |
| `high` | `Any` | Upper bound (inclusive) |
| `columns` | `list[str] \| None` | Columns to project; defaults to `*` |

Returns a **`BetweenFrame`** — a lazy object that executes the query only
when `.to_pandas()` is called.

### `BetweenFrame` methods

| Method | Description |
|--------|-------------|
| `.where(condition, params=None)` | Add extra filter conditions |
| `.limit(n)` | Restrict result to *n* rows |
| `.to_pandas()` | Execute and return a `pandas.DataFrame` |
