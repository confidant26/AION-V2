from calendar import monthrange
from datetime import date


DEFAULT_PERIOD_TOLERANCE_DAYS = 7


def canonical_period_end_date(
    value: date,
    *,
    tolerance_days: int = (
        DEFAULT_PERIOD_TOLERANCE_DAYS
    ),
) -> date:
    if tolerance_days < 0:
        raise ValueError(
            "Period tolerance cannot be negative."
        )

    current_month_end = date(
        value.year,
        value.month,
        monthrange(
            value.year,
            value.month,
        )[1],
    )

    if value.month == 1:
        previous_year = (
            value.year - 1
        )
        previous_month = 12
    else:
        previous_year = value.year
        previous_month = (
            value.month - 1
        )

    previous_month_end = date(
        previous_year,
        previous_month,
        monthrange(
            previous_year,
            previous_month,
        )[1],
    )

    if value.month == 12:
        next_year = (
            value.year + 1
        )
        next_month = 1
    else:
        next_year = value.year
        next_month = (
            value.month + 1
        )

    next_month_end = date(
        next_year,
        next_month,
        monthrange(
            next_year,
            next_month,
        )[1],
    )

    candidates = (
        previous_month_end,
        current_month_end,
        next_month_end,
    )

    nearest = min(
        candidates,
        key=lambda candidate: abs(
            (
                candidate
                - value
            ).days
        ),
    )

    distance = abs(
        (
            nearest
            - value
        ).days
    )

    if distance <= tolerance_days:
        return nearest

    return value


def period_dates_match(
    left: date,
    right: date,
    *,
    tolerance_days: int = (
        DEFAULT_PERIOD_TOLERANCE_DAYS
    ),
) -> bool:
    return (
        canonical_period_end_date(
            left,
            tolerance_days=(
                tolerance_days
            ),
        )
        == canonical_period_end_date(
            right,
            tolerance_days=(
                tolerance_days
            ),
        )
    )