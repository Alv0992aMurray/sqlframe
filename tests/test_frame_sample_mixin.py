import pytest
from sqlframe.frame_sample_mixin import SampleMixin


# ---------------------------------------------------------------------------
# Minimal fake objects
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql, params=None):
        import pandas as pd
        self.last_sql = sql
        self.last_params = params
        return pd.DataFrame({"id": [1, 2, 3]})


class FakeFrame(SampleMixin):
    """Minimal frame that includes the SampleMixin."""

    def __init__(self, conn, table="users"):
        self._conn = conn
        self._table = table
        self._wheres = []
        self._limit = None

    def _build_sql(self):
        return f"SELECT * FROM {self._table}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    return FakeConn()


@pytest.fixture
def frame(conn):
    return FakeFrame(conn)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sample_n_returns_sample_frame(frame):
    from sqlframe.sampling import SampleFrame
    result = frame.sample(n=10)
    assert isinstance(result, SampleFrame)


def test_sample_frac_returns_sample_frame(frame):
    from sqlframe.sampling import SampleFrame
    result = frame.sample(frac=0.25)
    assert isinstance(result, SampleFrame)


def test_sample_n_and_frac_raises(frame):
    with pytest.raises(ValueError, match="not both"):
        frame.sample(n=5, frac=0.1)


def test_sample_neither_raises(frame):
    with pytest.raises(ValueError, match="must be provided"):
        frame.sample()


def test_sample_invalid_frac_raises(frame):
    with pytest.raises(ValueError, match="range"):
        frame.sample(frac=1.5)


def test_sample_zero_frac_raises(frame):
    with pytest.raises(ValueError, match="range"):
        frame.sample(frac=0.0)


def test_sample_negative_n_raises(frame):
    with pytest.raises(ValueError, match="positive integer"):
        frame.sample(n=0)


def test_sample_n_stores_attributes(frame):
    sf = frame.sample(n=50)
    assert sf._n == 50
    assert sf._frac is None


def test_sample_frac_stores_attributes(frame):
    sf = frame.sample(frac=0.1)
    assert sf._frac == 0.1
    assert sf._n is None


def test_sample_seed_forwarded(frame):
    sf = frame.sample(n=10, seed=42)
    assert sf._seed == 42


def test_sample_to_pandas_calls_conn(frame, conn):
    sf = frame.sample(n=5)
    df = sf.to_pandas()
    assert conn.last_sql is not None
    assert len(df) == 3  # FakeConn always returns 3 rows
