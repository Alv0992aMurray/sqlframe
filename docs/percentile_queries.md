# Percentile / Quantile Queries

The `percentile` method lets you compute SQL percentile aggregations against a
live database without pulling the entire table into memory first.

## Basic usage

```python
import sqlframe

conn = sqlframe.connect("postgresql://user:pass@localhost/mydb")
df = sqlframe.read_table(conn, "employees")

# Median salary
median = df.percentile("salary", 0.5).to_pandas()
print(median)
```

## Multiple percentiles in one query

Pass a list of floats to compute several quantiles in a single round-trip:

```python
quartiles = df.percentile("salary", [0.25, 0.5, 0.75]).to_pandas()
print(quartiles)
```

The resulting DataFrame will have one column per requested percentile, named
after the value (e.g. `p0_25`, `p0_5`, `p0_75`).

## Filtering before computing

Chain `.where()` to restrict the rows used in the calculation:

```python
eng_median = (
    df.percentile("salary", 0.5)
      .where("department = 'engineering'")
      .to_pandas()
)
```

Alternatively, filter the parent frame first — the WHERE clause is inherited
automatically:

```python
eng_df = df.where("department = 'engineering'")
eng_median = eng_df.percentile("salary", 0.5).to_pandas()
```

## Interpolation modes

The `interpolation` parameter is passed through to the underlying SQL
`PERCENTILE_CONT … WITHIN GROUP` expression.  Supported values:

| Value | Behaviour |
|-------|-----------|
| `"linear"` (default) | Standard continuous interpolation |
| `"lower"` | Returns the lower of the two surrounding values |
| `"higher"` | Returns the higher of the two surrounding values |
| `"midpoint"` | Average of the two surrounding values |
| `"nearest"` | Nearest value |

```python
lower_quartile = df.percentile("salary", 0.25, interpolation="lower").to_pandas()
```

## Notes

- Percentile values must be in the range **[0, 1]**.
- At least one percentile value must be supplied.
- The generated SQL uses the ANSI `PERCENTILE_CONT … WITHIN GROUP` syntax
  supported by PostgreSQL, DuckDB, and most modern analytical databases.
  MySQL / SQLite do **not** support this syntax natively.
