# Schema Inspection

SqlFrame can introspect the schema of any table you're querying, giving you
column names and data types without leaving your Python session.

## Quick start

```python
import sqlframe

conn = sqlframe.Connection.from_url("postgresql://user:pass@localhost/mydb")
df = sqlframe.read_table("orders", conn=conn)

# Fetch schema (queries information_schema.columns once, then caches)
schema = df.schema()
print(schema)
# TableSchema(orders):
#   <ColumnInfo id: integer NOT NULL>
#   <ColumnInfo customer_id: integer>
#   <ColumnInfo total: numeric>
#   <ColumnInfo created_at: timestamp without time zone>
```

## Column names

```python
df.column_names()
# ['id', 'customer_id', 'total', 'created_at']
```

## Data types

```python
df.dtypes()
# {'id': 'integer', 'customer_id': 'integer', 'total': 'numeric',
#  'created_at': 'timestamp without time zone'}
```

## Forcing a refresh

Schema results are cached per connection. Pass `force=True` to re-query:

```python
df.schema(force=True)
```

Or clear the entire cache:

```python
conn._schema_inspector.clear_cache()
```

## API reference

### `TableSchema`

| Attribute | Type | Description |
|-----------|------|-------------|
| `table` | `str` | Table name |
| `columns` | `list[ColumnInfo]` | Ordered column metadata |

Methods: `column_names()`, `dtypes()`

### `ColumnInfo`

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Column name |
| `dtype` | `str` | SQL data type string |
| `nullable` | `bool` | Whether the column allows NULL |
| `primary_key` | `bool` | Whether the column is a PK |

### `SchemaInspector`

Low-level class that powers the mixin. Constructed automatically on first use
and stored as `conn._schema_inspector`.
