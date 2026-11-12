"""Reuse the cold CLI harness with this validation ledger; never mutate its parent."""
from development.secret_hunter_response import runtime_checks as harness
from .accounting import reserve, finish

if __name__ == '__main__':
    harness.reserve = reserve
    harness.finish = finish
    harness.main()
