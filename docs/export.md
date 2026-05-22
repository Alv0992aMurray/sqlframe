# Export

`sqlframe` lets you serialise query results to **CSV**, **TSV**, or **JSON**
without ever leaving your Python session.

## Quick start

```python
import sqlframe

conn = sqlframe.Connection.from_url("sqlite:///mydb.sqlite")
frame = sqlframe.read_table(conn, "orders")

# --- CSV ---
# write to disk
frame.export("csv", path="/tmp/orders.csv")

# get content as a string (no file written)
result = frame.export("csv")
print(result.content)

# --- JSON ---
result = frame.export("json", indent=4)
print(result.content)

# --- TSV ---
frame.export("tsv", path="/tmp/orders.tsv")
```

## API

### `ExportMixin.export(fmt, path=None, **kwargs)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fmt` | `str` | `'csv'` | One of `'csv'`, `'json'`, `'tsv'` |
| `path` | `str \| None` | `None` | Destination file path. `None` = in-memory |
| `**kwargs` | | | Forwarded to the underlying pandas method |

Returns an `ExportResult` with:

- `.path` – the file path written (or `None`).
- `.content` – serialised string when no path was given (or `None`).
- `.fmt` – the format used.

## Supported formats

| Format | Pandas method | Notes |
|--------|--------------|-------|
| `csv` | `DataFrame.to_csv` | Comma-separated |
| `tsv` | `DataFrame.to_csv` | Tab-separated |
| `json` | `DataFrame.to_json` | Default orient: `records` |
