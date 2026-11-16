"""
Generate a realistic synthetic consumer credit & loan dataset.

Why synthetic? Real consumer loan data with payment histories is private (PII),
so this module creates borrowers, loans, and monthly installment records that
behave like the real thing: lower credit scores pay late more often, and loans
that start missing payments tend to keep missing them (roll rates).

Outputs (CSV) to data/raw/:
    borrowers.csv, loans.csv, payments.csv

Usage:
    python extract/generate_loans.py --borrowers 5000 --as-of 2026-10-31
"""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

STATES = ["TX", "CA", "FL", "NY", "IL", "GA", "OH", "NC", "AZ", "WA"]
PRODUCTS = {
    # product: (min_amt, max_amt, terms, base_apr)
    "personal": (2_000, 35_000, [24, 36, 48, 60], 0.11),
    "auto": (8_000, 55_000, [36, 48, 60, 72], 0.07),
    "student": (5_000, 40_000, [60, 120], 0.055),
}


def make_borrowers(n: int, rng: np.random.Generator, as_of: date) -> pd.DataFrame:
    credit_score = np.clip(rng.normal(690, 70, n), 300, 850).round().astype(int)
    # income loosely correlated with credit score
    income = np.clip(rng.lognormal(10.9, 0.45, n) * (credit_score / 690), 15_000, 400_000).round(-2)
    created = pd.to_datetime(as_of) - pd.to_timedelta(rng.integers(120, 1500, n), unit="D")
    return pd.DataFrame(
        {
            "borrower_id": [f"B{i:06d}" for i in range(1, n + 1)],
            "state": rng.choice(STATES, n),
            "annual_income": income,
            "credit_score": credit_score,
            "employment_years": rng.integers(0, 30, n),
            "created_at": created.date,
        }
    )


def amortization(principal: float, apr: float, term: int) -> float:
    r = apr / 12
    return principal * r / (1 - (1 + r) ** -term)


def make_loans(borrowers: pd.DataFrame, rng: np.random.Generator, as_of: date) -> pd.DataFrame:
    rows = []
    loan_seq = 1
    for b in borrowers.itertuples(index=False):
        for _ in range(rng.choice([1, 1, 1, 2, 3])):
            product = rng.choice(list(PRODUCTS))
            lo, hi, terms, base_apr = PRODUCTS[product]
            principal = round(float(rng.uniform(lo, hi)), -1)
            term = int(rng.choice(terms))
            # risk-based pricing: worse score -> higher APR
            apr = round(base_apr + max(0, (720 - b.credit_score)) * 0.0004 + rng.normal(0, 0.01), 4)
            apr = float(np.clip(apr, 0.03, 0.36))
            orig = pd.Timestamp(b.created_at) + pd.Timedelta(days=int(rng.integers(0, 90)))
            if orig.date() >= as_of:
                continue
            rows.append(
                {
                    "loan_id": f"L{loan_seq:07d}",
                    "borrower_id": b.borrower_id,
                    "product_type": product,
                    "principal": principal,
                    "apr": apr,
                    "term_months": term,
                    "monthly_payment": round(amortization(principal, apr, term), 2),
                    "origination_date": orig.date(),
                }
            )
            loan_seq += 1
    return pd.DataFrame(rows)


def make_payments(
    loans: pd.DataFrame, borrowers: pd.DataFrame, rng: np.random.Generator, as_of: date
) -> pd.DataFrame:
    score = borrowers.set_index("borrower_id")["credit_score"]
    as_of_ts = pd.Timestamp(as_of)
    rows = []
    pay_seq = 1
    for ln in loans.itertuples(index=False):
        # baseline monthly probability of missing a payment, driven by credit score
        p_miss = float(np.clip(0.002 + (700 - score[ln.borrower_id]) * 0.00025, 0.001, 0.12))
        balance = ln.principal
        r = ln.apr / 12
        missed_streak = 0
        charged_off = False
        for k in range(1, ln.term_months + 1):
            due = pd.Timestamp(ln.origination_date) + pd.DateOffset(months=k)
            if due > as_of_ts:
                break
            interest = round(balance * r, 2)
            principal_part = round(min(ln.monthly_payment - interest, balance), 2)

            # once delinquent, borrowers are much more likely to stay delinquent
            p = 0.75 if missed_streak > 0 else p_miss
            missed = charged_off or rng.random() < p
            if missed:
                missed_streak += 1
                if missed_streak >= 6:
                    charged_off = True
                paid_date, amount_paid = None, 0.0
            else:
                missed_streak = 0
                # most pay on time, some a few days late (still within grace period)
                days = int(rng.choice([-3, -1, 0, 0, 0, 2, 5, 12]))
                paid_ts = due + pd.Timedelta(days=days)
                if paid_ts > as_of_ts:
                    paid_date, amount_paid = None, 0.0
                else:
                    paid_date, amount_paid = paid_ts.date(), ln.monthly_payment
                    balance = round(balance - principal_part, 2)

            rows.append(
                {
                    "payment_id": f"P{pay_seq:09d}",
                    "loan_id": ln.loan_id,
                    "installment_number": k,
                    "due_date": due.date(),
                    "amount_due": ln.monthly_payment,
                    "principal_component": principal_part,
                    "interest_component": interest,
                    "paid_date": paid_date,
                    "amount_paid": amount_paid,
                }
            )
            pay_seq += 1
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--borrowers", type=int, default=5000)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 10, 31))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    borrowers = make_borrowers(args.borrowers, rng, args.as_of)
    loans = make_loans(borrowers, rng, args.as_of)
    payments = make_payments(loans, borrowers, rng, args.as_of)

    for name, df in {"borrowers": borrowers, "loans": loans, "payments": payments}.items():
        path = args.out / f"{name}.csv"
        df.to_csv(path, index=False)
        log.info("wrote %s rows -> %s", f"{len(df):,}", path)


if __name__ == "__main__":
    main()
