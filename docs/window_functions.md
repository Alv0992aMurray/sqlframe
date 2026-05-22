# Window Functions

SqlFrame exposes SQL window functions through the `sqlframe.window` module and
the `.window()` method available on every `SqlFrame`.

## Quick start

```python
import sqlframe
from sqlframe.window import rank_over, row_number_over, lag_over, lead_over

conn = sqlframe.Connection.from_url("postgresql://user:pass@localhost/mydb")

df = (
    conn.read_table("sales")
    .select("dept", "employee", "revenue")
    .window(
        window_cols=[
            rank_over(partition_by=["dept"], order_by=["revenue DESC"]),
        ],
        extra_cols=["dept", "employee", "revenue"],
    )
    .where("rank = 1")          # filter after the window is applied
    .to_pandas()
)
print(df)
```

The call chain above generates SQL similar to:

```sql
SELECT dept, employee, revenue,
       RANK() OVER (PARTITION BY dept ORDER BY revenue DESC) AS rank
FROM (
    SELECT dept, employee, revenue
    FROM sales
) AS _window_base
WHERE rank = 1
```

## Available helpers

| Helper | SQL produced |
|---|---|
| `rank_over(partition_by, order_by)` | `RANK() OVER (...)  AS rank` |
| `row_number_over(partition_by, order_by)` | `ROW_NUMBER() OVER (...) AS row_number` |
| `lag_over(col, offset, partition_by, order_by)` | `LAG(col, offset) OVER (...) AS lag_col` |
| `lead_over(col, offset, partition_by, order_by)` | `LEAD(col, offset) OVER (...) AS lead_col` |

## WindowSpec

For custom expressions you can use `WindowSpec` directly:

```python
from sqlframe.window import WindowSpec

spec = WindowSpec(partition_by=["region"], order_by=["date DESC"])
custom_expr = f"SUM(revenue) {spec._render()} AS running_total"

df = (
    conn.read_table("sales")
    .window(window_cols=[custom_expr], extra_cols=["region", "date", "revenue"])
    .to_pandas()
)
```

## WindowFrame API

`WindowFrame` supports a small fluent API before execution:

```python
wf = frame.window(window_cols=[...], extra_cols=[...])
wf.where("rank <= 5").limit(100).to_pandas()
```
