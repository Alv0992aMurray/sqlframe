# Filling NULL Values

SqlFrame provides a `.fillna()` method (available on `SqlFrame` and other frame
types) that generates `COALESCE`-based SQL to replace `NULL` values without
pulling data into memory first.

## Basic Usage

```python
import sqlframe

conn = sqlframe.Connection.from_url("duckdb:///warehouse.db")
df = sqlframe.read_table(conn, "sales")

# Replace NULLs in a single column
result = df.fillna({"revenue": 0}).to_pandas()
```

## Scalar Fill (all columns)

Pass a scalar value and every column in the table will be wrapped with
`COALESCE`:

```python
result = df.fillna(0).to_pandas()
```

> **Note:** When using a scalar without `subset`, sqlframe must know the column
> list up front. If it cannot introspect the schema automatically, pass a
> `subset` list or use the dict form.

## Scalar Fill (subset of columns)

```python
result = df.fillna(0, subset=["revenue", "quantity"]).to_pandas()
```

## Dict Fill (per-column values)

```python
result = df.fillna({
    "revenue": 0,
    "region": "unknown",
    "is_active": False,
}).to_pandas()
```

## Chaining with Other Methods

`FillNaFrame` supports `.where()` and `.limit()` for further narrowing:

```python
result = (
    df.fillna({"revenue": 0})
      .where("year = 2024")
      .limit(100)
      .to_pandas()
)
```

## Generated SQL

For the dict example above, sqlframe emits:

```sql
SELECT * REPLACE (
    COALESCE(revenue, 0) AS revenue,
    COALESCE(region, 'unknown') AS region,
    COALESCE(is_active, FALSE) AS is_active
)
FROM sales
```

The `* REPLACE` syntax is supported by DuckDB and BigQuery. For databases that
do not support it, consider using `.select()` with explicit `COALESCE` expressions
or opening an issue requesting dialect support.
