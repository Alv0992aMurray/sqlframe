# Distinct Queries

`sqlframe` provides a `DistinctFrame` class (and the accompanying
`DistinctMixin`) to make `SELECT DISTINCT` queries as ergonomic as the rest of
the library.

## Quick start

```python
import sqlframe

conn = sqlframe.Connection.from_url("postgresql://user:pass@localhost/mydb")

# Distinct values for a single column
statuses = (
    sqlframe.read_table(conn, "orders")
    .distinct(["status"])
    .to_pandas()
)

print(statuses)
```

## Selecting multiple columns

Pass a list of column names to get distinct *combinations*:

```python
regions = (
    sqlframe.read_table(conn, "orders")
    .distinct(["region", "status"])
    .to_pandas()
)
```

Omit the argument (or pass an empty list) to select all columns:

```python
all_distinct = (
    sqlframe.read_table(conn, "orders")
    .distinct()
    .to_pandas()
)
```

## Filtering distinct results

`DistinctFrame` exposes the same `.where()` interface as `SqlFrame`:

```python
active_statuses = (
    sqlframe.read_table(conn, "orders")
    .distinct(["status"])
    .where("active = 1")
    .to_pandas()
)
```

Parameterised queries are also supported:

```python
big_orders = (
    sqlframe.read_table(conn, "orders")
    .distinct(["customer_id"])
    .where("amount > %s", params=[500])
    .to_pandas()
)
```

## Limiting results

```python
top10 = (
    sqlframe.read_table(conn, "orders")
    .distinct(["customer_id"])
    .limit(10)
    .to_pandas()
)
```

## Generated SQL

You can inspect the SQL that will be executed without hitting the database:

```python
df = (
    sqlframe.read_table(conn, "orders")
    .distinct(["status"])
    .where("active = 1")
    .limit(5)
)
print(repr(df))
# DistinctFrame(sql='SELECT DISTINCT status FROM orders WHERE active = 1 LIMIT 5')
```
