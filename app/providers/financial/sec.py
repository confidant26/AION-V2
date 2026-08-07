from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
import gzip
import json
import zlib
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.fiscal_period import (
    canonical_period_end_date,
)
from app.providers.financial.base import (
    FinancialDataProvider,
)
from app.providers.resilience import (
    run_sync_with_retry,
)


class SecFinancialProvider(
    FinancialDataProvider
):
    provider_name = "sec"

    TICKERS_URL = (
        "https://www.sec.gov/files/"
        "company_tickers.json"
    )

    COMPANY_FACTS_URL = (
        "https://data.sec.gov/api/xbrl/"
        "companyfacts/CIK{cik}.json"
    )

    REVENUE_TAGS = (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    )

    COST_OF_REVENUE_TAGS = (
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
    )

    GROSS_PROFIT_TAGS = (
        "GrossProfit",
    )

    OPERATING_EXPENSE_TAGS = (
        "OperatingExpenses",
        "OperatingCostsAndExpenses",
    )

    OPERATING_INCOME_TAGS = (
        "OperatingIncomeLoss",
    )

    PRETAX_INCOME_TAGS = (
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
    )

    TAX_PROVISION_TAGS = (
        "IncomeTaxExpenseBenefit",
    )

    NET_INCOME_TAGS = (
        "NetIncomeLoss",
        "ProfitLoss",
    )

    DILUTED_SHARES_TAGS = (
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    )

    DILUTED_EPS_TAGS = (
        "EarningsPerShareDiluted",
    )

    ADDITIVE_FIELDS = (
        "total_revenue",
        "cost_of_revenue",
        "gross_profit",
        "operating_expense",
        "operating_income",
        "pretax_income",
        "tax_provision",
        "net_income",
    )

    MAX_ANNUAL_STATEMENTS = 4
    MAX_QUARTERLY_STATEMENTS = 5

    async def get_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        clean_symbol = (
            symbol.strip().upper()
        )

        if not clean_symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        return await run_sync_with_retry(
            lambda: (
                self._fetch_income_statements(
                    clean_symbol
                )
            ),
            provider_name="SEC EDGAR",
            operation_name=(
                f"income statements for "
                f"{clean_symbol}"
            ),
        )

    def _fetch_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        self._validate_user_agent()

        cik = self._resolve_cik(
            symbol
        )

        company_facts = (
            self._get_json(
                self.COMPANY_FACTS_URL.format(
                    cik=cik
                )
            )
        )

        statements = (
            self._build_statements(
                company_facts
            )
        )

        if not statements:
            raise ValueError(
                f"SEC income statements not found "
                f"for symbol: {symbol}"
            )

        annual_statements = sorted(
            [
                statement
                for statement in statements
                if statement[
                    "period_type"
                ] == "annual"
            ],
            key=lambda statement: (
                statement[
                    "period_end_date"
                ]
            ),
            reverse=True,
        )[
            :self.MAX_ANNUAL_STATEMENTS
        ]

        quarterly_statements = sorted(
            [
                statement
                for statement in statements
                if statement[
                    "period_type"
                ] == "quarterly"
            ],
            key=lambda statement: (
                statement[
                    "period_end_date"
                ]
            ),
            reverse=True,
        )[
            :self.MAX_QUARTERLY_STATEMENTS
        ]

        if (
            len(annual_statements) < 2
            or len(
                quarterly_statements
            ) < 4
        ):
            raise ValueError(
                f"SEC financial history is incomplete "
                f"for symbol: {symbol}"
            )

        annual_statements = (
            self._normalize_period_dates(
                annual_statements
            )
        )

        quarterly_statements = (
            self._normalize_period_dates(
                quarterly_statements
            )
        )

        return (
            annual_statements
            + quarterly_statements
        )

    @staticmethod
    def _normalize_period_dates(
        statements: list[dict],
    ) -> list[dict]:
        normalized: list[dict] = []

        seen: set[
            tuple[
                str,
                date,
            ]
        ] = set()

        for statement in statements:
            source_date = statement.get(
                "period_end_date"
            )

            if not isinstance(
                source_date,
                date,
            ):
                continue

            canonical_date = (
                canonical_period_end_date(
                    source_date
                )
            )

            key = (
                statement[
                    "period_type"
                ],
                canonical_date,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            normalized_statement = {
                **statement,
                "period_end_date": (
                    canonical_date
                ),
            }

            normalized.append(
                normalized_statement
            )

        return sorted(
            normalized,
            key=lambda statement: (
                statement[
                    "period_end_date"
                ]
            ),
            reverse=True,
        )

    @staticmethod
    def _validate_user_agent() -> None:
        if not (
            settings
            .sec_user_agent
            .strip()
        ):
            raise ValueError(
                "SEC_USER_AGENT must be configured "
                "before using the SEC provider."
            )

    @classmethod
    @lru_cache(maxsize=1)
    def _ticker_map(
        cls,
    ) -> dict[str, str]:
        provider = cls()

        provider._validate_user_agent()

        payload = provider._get_json(
            cls.TICKERS_URL
        )

        mapping: dict[
            str,
            str,
        ] = {}

        for item in payload.values():
            ticker = str(
                item.get(
                    "ticker",
                    "",
                )
            ).strip().upper()

            cik_value = item.get(
                "cik_str"
            )

            if (
                not ticker
                or cik_value is None
            ):
                continue

            mapping[ticker] = str(
                cik_value
            ).zfill(10)

        return mapping

    def _resolve_cik(
        self,
        symbol: str,
    ) -> str:
        cik = (
            self._ticker_map()
            .get(
                symbol
            )
        )

        if cik is None:
            raise ValueError(
                f"SEC CIK not found for symbol: "
                f"{symbol}"
            )

        return cik

    def _get_json(
        self,
        url: str,
    ) -> dict:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    settings
                    .sec_user_agent
                ),
                "Accept": (
                    "application/json"
                ),
                "Accept-Encoding": (
                    "gzip, deflate"
                ),
            },
        )

        with urlopen(
            request,
            timeout=(
                settings
                .provider_timeout_seconds
            ),
        ) as response:
            raw_data = (
                response.read()
            )

            content_encoding = (
                response.headers.get(
                    "Content-Encoding",
                    "",
                )
                .strip()
                .lower()
            )

            if (
                content_encoding
                == "gzip"
            ):
                raw_data = (
                    gzip.decompress(
                        raw_data
                    )
                )

            elif (
                content_encoding
                == "deflate"
            ):
                try:
                    raw_data = (
                        zlib.decompress(
                            raw_data
                        )
                    )

                except zlib.error:
                    raw_data = (
                        zlib.decompress(
                            raw_data,
                            -zlib.MAX_WBITS,
                        )
                    )

            return json.loads(
                raw_data.decode(
                    "utf-8"
                )
            )

    def _build_statements(
        self,
        company_facts: dict,
    ) -> list[dict]:
        facts = (
            company_facts
            .get(
                "facts",
                {},
            )
            .get(
                "us-gaap",
                {},
            )
        )

        currency = (
            self._detect_currency(
                facts
            )
        )

        field_specs = {
            "total_revenue": (
                self.REVENUE_TAGS,
                "USD",
            ),
            "cost_of_revenue": (
                self.COST_OF_REVENUE_TAGS,
                "USD",
            ),
            "gross_profit": (
                self.GROSS_PROFIT_TAGS,
                "USD",
            ),
            "operating_expense": (
                self.OPERATING_EXPENSE_TAGS,
                "USD",
            ),
            "operating_income": (
                self.OPERATING_INCOME_TAGS,
                "USD",
            ),
            "pretax_income": (
                self.PRETAX_INCOME_TAGS,
                "USD",
            ),
            "tax_provision": (
                self.TAX_PROVISION_TAGS,
                "USD",
            ),
            "net_income": (
                self.NET_INCOME_TAGS,
                "USD",
            ),
            "diluted_average_shares": (
                self.DILUTED_SHARES_TAGS,
                "shares",
            ),
            "diluted_eps": (
                self.DILUTED_EPS_TAGS,
                "USD/shares",
            ),
        }

        annual_by_date: dict[
            date,
            dict,
        ] = {}

        quarterly_by_date: dict[
            date,
            dict,
        ] = {}

        for (
            field_name,
            (
                tags,
                preferred_unit,
            ),
        ) in field_specs.items():
            annual_values = (
                self._extract_values(
                    facts=facts,
                    tags=tags,
                    preferred_unit=(
                        preferred_unit
                    ),
                    period_type=(
                        "annual"
                    ),
                )
            )

            quarterly_values = (
                self._extract_values(
                    facts=facts,
                    tags=tags,
                    preferred_unit=(
                        preferred_unit
                    ),
                    period_type=(
                        "quarterly"
                    ),
                )
            )

            for (
                period_end,
                value,
            ) in annual_values.items():
                statement = (
                    annual_by_date
                    .setdefault(
                        period_end,
                        self._empty_statement(
                            period_end=(
                                period_end
                            ),
                            period_type=(
                                "annual"
                            ),
                            currency=(
                                currency
                            ),
                        ),
                    )
                )

                statement[
                    field_name
                ] = value

            for (
                period_end,
                value,
            ) in quarterly_values.items():
                statement = (
                    quarterly_by_date
                    .setdefault(
                        period_end,
                        self._empty_statement(
                            period_end=(
                                period_end
                            ),
                            period_type=(
                                "quarterly"
                            ),
                            currency=(
                                currency
                            ),
                        ),
                    )
                )

                statement[
                    field_name
                ] = value

        self._derive_fourth_quarters(
            annual_by_date=(
                annual_by_date
            ),
            quarterly_by_date=(
                quarterly_by_date
            ),
        )

        statements = [
            *annual_by_date.values(),
            *quarterly_by_date.values(),
        ]

        statements = [
            statement
            for statement in statements
            if self._has_core_data(
                statement
            )
        ]

        return sorted(
            statements,
            key=lambda statement: (
                statement[
                    "period_type"
                ]
                != "annual",
                statement[
                    "period_end_date"
                ],
            ),
            reverse=True,
        )

    @staticmethod
    def _empty_statement(
        *,
        period_end: date,
        period_type: str,
        currency: str | None,
    ) -> dict:
        return {
            "period_end_date": (
                period_end
            ),
            "period_type": (
                period_type
            ),
            "currency": currency,
            "total_revenue": None,
            "cost_of_revenue": None,
            "gross_profit": None,
            "operating_expense": None,
            "operating_income": None,
            "net_non_operating_interest_income_expense": (
                None
            ),
            "pretax_income": None,
            "tax_provision": None,
            "net_income": None,
            "diluted_average_shares": None,
            "diluted_eps": None,
        }

    def _extract_values(
        self,
        *,
        facts: dict,
        tags: tuple[
            str,
            ...,
        ],
        preferred_unit: str,
        period_type: str,
    ) -> dict[
        date,
        float,
    ]:
        concept = (
            self._find_concept(
                facts=facts,
                tags=tags,
            )
        )

        if concept is None:
            return {}

        units = concept.get(
            "units",
            {},
        )

        values = (
            self._choose_unit(
                units=units,
                preferred_unit=(
                    preferred_unit
                ),
            )
        )

        if not values:
            return {}

        candidates: dict[
            date,
            tuple[
                str,
                float,
            ],
        ] = {}

        for item in values:
            if item.get(
                "form"
            ) not in {
                "10-K",
                "10-K/A",
                "10-Q",
                "10-Q/A",
            }:
                continue

            end = self._to_date(
                item.get(
                    "end"
                )
            )

            start = self._to_date(
                item.get(
                    "start"
                )
            )

            value = item.get(
                "val"
            )

            if (
                end is None
                or value is None
            ):
                continue

            duration_days = (
                (
                    end
                    - start
                ).days
                if start is not None
                else None
            )

            if (
                period_type
                == "annual"
            ):
                if item.get(
                    "form"
                ) not in {
                    "10-K",
                    "10-K/A",
                }:
                    continue

                if (
                    duration_days
                    is not None
                    and not (
                        300
                        <= duration_days
                        <= 400
                    )
                ):
                    continue

            else:
                if item.get(
                    "form"
                ) not in {
                    "10-Q",
                    "10-Q/A",
                }:
                    continue

                if (
                    duration_days
                    is None
                    or not (
                        60
                        <= duration_days
                        <= 120
                    )
                ):
                    continue

            filed = str(
                item.get(
                    "filed",
                    "",
                )
            )

            try:
                numeric_value = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            existing = (
                candidates.get(
                    end
                )
            )

            if (
                existing is None
                or filed
                > existing[0]
            ):
                candidates[end] = (
                    filed,
                    numeric_value,
                )

        return {
            period_end: value
            for (
                period_end,
                (
                    _,
                    value,
                ),
            ) in candidates.items()
        }

    @staticmethod
    def _find_concept(
        *,
        facts: dict,
        tags: tuple[
            str,
            ...,
        ],
    ) -> dict | None:
        for tag in tags:
            concept = facts.get(
                tag
            )

            if concept is not None:
                return concept

        return None

    @staticmethod
    def _choose_unit(
        *,
        units: dict,
        preferred_unit: str,
    ) -> list[dict]:
        if preferred_unit in units:
            return units[
                preferred_unit
            ]

        normalized = {
            key.lower(): value
            for (
                key,
                value,
            ) in units.items()
        }

        requested = (
            preferred_unit
            .lower()
        )

        if requested in normalized:
            return normalized[
                requested
            ]

        if (
            preferred_unit
            == "USD/shares"
        ):
            for (
                unit_name,
                unit_values,
            ) in units.items():
                lowered = (
                    unit_name
                    .lower()
                )

                if (
                    "usd"
                    in lowered
                    and "share"
                    in lowered
                ):
                    return unit_values

        return []

    def _derive_fourth_quarters(
        self,
        *,
        annual_by_date: dict[
            date,
            dict,
        ],
        quarterly_by_date: dict[
            date,
            dict,
        ],
    ) -> None:
        quarter_dates = sorted(
            quarterly_by_date
        )

        for (
            annual_date,
            annual_statement,
        ) in annual_by_date.items():
            previous_quarters = [
                quarter_date
                for quarter_date
                in quarter_dates
                if (
                    quarter_date
                    < annual_date
                    and (
                        annual_date
                        - quarter_date
                    ).days
                    <= 300
                )
            ]

            if (
                len(
                    previous_quarters
                )
                < 3
            ):
                continue

            first_three = (
                previous_quarters[
                    -3:
                ]
            )

            if (
                annual_date
                - first_three[0]
            ).days > 300:
                continue

            q4 = (
                quarterly_by_date
                .setdefault(
                    annual_date,
                    self._empty_statement(
                        period_end=(
                            annual_date
                        ),
                        period_type=(
                            "quarterly"
                        ),
                        currency=(
                            annual_statement
                            .get(
                                "currency"
                            )
                        ),
                    ),
                )
            )

            for field_name in (
                self.ADDITIVE_FIELDS
            ):
                annual_value = (
                    annual_statement
                    .get(
                        field_name
                    )
                )

                quarter_values = [
                    quarterly_by_date[
                        quarter_date
                    ].get(
                        field_name
                    )
                    for quarter_date
                    in first_three
                ]

                if (
                    annual_value is None
                    or any(
                        value is None
                        for value
                        in quarter_values
                    )
                ):
                    continue

                q4[
                    field_name
                ] = (
                    float(
                        annual_value
                    )
                    - sum(
                        float(
                            value
                        )
                        for value
                        in quarter_values
                    )
                )

    @staticmethod
    def _detect_currency(
        facts: dict,
    ) -> str | None:
        for tag in (
            *SecFinancialProvider.REVENUE_TAGS,
            *SecFinancialProvider.NET_INCOME_TAGS,
        ):
            concept = (
                facts.get(
                    tag
                )
            )

            if concept is None:
                continue

            units = concept.get(
                "units",
                {},
            )

            if "USD" in units:
                return "USD"

            for unit_name in units:
                if (
                    len(
                        unit_name
                    ) == 3
                    and unit_name
                    .isalpha()
                ):
                    return (
                        unit_name
                        .upper()
                    )

        return None

    @staticmethod
    def _has_core_data(
        statement: dict,
    ) -> bool:
        return any(
            statement.get(
                field_name
            )
            is not None
            for field_name in (
                "total_revenue",
                "gross_profit",
                "operating_income",
                "pretax_income",
                "net_income",
            )
        )

    @staticmethod
    def _to_date(
        value,
    ) -> date | None:
        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        try:
            return date.fromisoformat(
                str(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return None