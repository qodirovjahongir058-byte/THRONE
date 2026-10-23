
from datetime import date, timedelta

import pytest

from database import (
    claim_daily_bonus,
    ensure_user,
    get_user,
    init_db,
)


@pytest.fixture
async def db_path(tmp_path):
    """Har bir test uchun alohida vaqtinchalik baza."""
    path = str(tmp_path / "throne_test.db")
    await init_db(path)
    return path


@pytest.mark.asyncio
async def test_daily_bonus_can_be_claimed_once_per_day(db_path):
    await ensure_user(db_path, 1001, "test_user", "Test")
    today = date(2026, 10, 23)

    first = await claim_daily_bonus(db_path, 1001, today)
    second = await claim_daily_bonus(db_path, 1001, today)

    assert first["ok"] is True
    assert first["day"] == 1
    assert first["oltin"] == 100
    assert second["ok"] is False
    assert second["reason"] == "already_claimed"

    user = await get_user(db_path, 1001)
    assert user["oltin"] == 100


@pytest.mark.asyncio
async def test_daily_bonus_streak_increases(db_path):
    await ensure_user(db_path, 1002, "streak_user", "Streak")
    start = date(2026, 10, 1)

    for day in range(1, 8):
        result = await claim_daily_bonus(
            db_path,
            1002,
            start + timedelta(days=day - 1),
        )
        assert result["ok"] is True
        assert result["day"] == day

    user = await get_user(db_path, 1002)
    assert user["daily_streak"] == 7
    assert user["oltin"] == 2300
    assert user["xp"] == 60


@pytest.mark.asyncio
async def test_missing_a_day_resets_streak(db_path):
    await ensure_user(db_path, 1003, "reset_user", "Reset")
    start = date(2026, 10, 1)

    first = await claim_daily_bonus(db_path, 1003, start)
    second = await claim_daily_bonus(
        db_path,
        1003,
        start + timedelta(days=1),
    )
    after_gap = await claim_daily_bonus(
        db_path,
        1003,
        start + timedelta(days=3),
    )

    assert first["day"] == 1
    assert second["day"] == 2
    assert after_gap["ok"] is True
    assert after_gap["day"] == 1
    assert after_gap["oltin"] == 100


@pytest.mark.asyncio
async def test_daily_bonus_requires_existing_user(db_path):
    result = await claim_daily_bonus(
        db_path,
        999999,
        date(2026, 10, 23),
    )

    assert result["ok"] is False
    assert result["reason"] == "user_not_found"
  
