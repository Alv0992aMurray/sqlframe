import pandas as pd
import pytest
from sqlframe.describe import DescribeFrame


# ---------------------------------------------------------------------------
# Fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self, return_df: pd.DataFrame):
        self._return_df = return_df
        self.last_sql: str = ""

    def query(self, sql: str) -> pd.DataFrame:
        self.last_sql = sql
        return self._return_df


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stat_row() -> pd.DataFrame:
    """Simulated single-row result from the DB."""
    return pd.DataFrame(
        [
            {
                "count__age": 100,
                "mean__age": 35.2,
                "min__age": 18,
                "max__age": 72,
                "stddev__age": 12.4,
                "count__salary": 100,
                "mean__salary": 55000.0,
                "min__salary": 20000,
                "max__salary": 120000,
                "stddev__salary": 18000.0,
            }
        ]
    )


@pytest.fixture()
def describe_frame(stat_row):
    conn = FakeConn(stat_row)
    return DescribeFrame(
        conn=conn,
        source_sql="SELECT age, salary FROM employees",
        columns=["age", "salary"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_build_sql_contains_agg_expressions(describe_frame):
    sql = describe_frame._build_sql()
    assert "AVG(age)" in sql
    assert "COUNT(salary)" in sql
    assert "MIN(age)" in sql
    assert "MAX(salary)" in sql
    assert "STDDEV(age)" in sql


def test_build_sql_wraps_source_in_subquery(describe_frame):
    sql = describe_frame._build_sql()
    assert "FROM (SELECT age, salary FROM employees) AS _describe_src" in sql


def test_to_pandas_returns_dataframe(describe_frame):
    result = describe_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)


def test_to_pandas_columns_match_input_columns(describe_frame):
    result = describe_frame.to_pandas()
    assert set(result.columns) == {"age", "salary"}


def test_to_pandas_index_contains_stats(describe_frame):
    result = describe_frame.to_pandas()
    assert "mean" in result.index
    assert "count" in result.index
    assert "min" in result.index
    assert "max" in result.index


def test_to_pandas_values_are_correct(describe_frame):
    result = describe_frame.to_pandas()
    assert result.loc["mean", "age"] == pytest.approx(35.2)
    assert result.loc["max", "salary"] == 120000


def test_no_columns_raises_value_error():
    conn = FakeConn(pd.DataFrame())
    df = DescribeFrame(conn=conn, source_sql="SELECT 1", columns=[])
    with pytest.raises(ValueError, match="at least one column"):
        df._build_sql()


def test_percentile_included_in_sql():
    conn = FakeConn(pd.DataFrame([{"count__score": 50, "mean__score": 5.0,
                                    "min__score": 1, "max__score": 10,
                                    "stddev__score": 2.0,
                                    "pct0_5__score": 5.0}]))
    df = DescribeFrame(
        conn=conn,
        source_sql="SELECT score FROM tests",
        columns=["score"],
        percentiles=[0.5],
    )
    sql = df._build_sql()
    assert "PERCENTILE_CONT(0.5)" in sql
    assert "pct0_5__score" in sql


def test_empty_result_returns_empty_dataframe():
    conn = FakeConn(pd.DataFrame())
    df = DescribeFrame(conn=conn, source_sql="SELECT age FROM t", columns=["age"])
    result = df.to_pandas()
    assert result.empty
