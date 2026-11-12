"""Execute one charged game in an isolated, externally supervised process."""
import faulthandler
import json
from pathlib import Path
import sys


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    faulthandler.enable()
    faulthandler.dump_traceback_later(request['timeout_seconds'] * .9)
    try:
        from development.secret_hunter_mcgs.train import worker
        worker(request['task'], request['result_path'], request['full_cli'])
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
