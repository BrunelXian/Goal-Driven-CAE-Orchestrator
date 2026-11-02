"""AOO read-only inspection. Host mutation requires a qualified injected port."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('capabilities')
    inspect = sub.add_parser('inspect')
    inspect.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'capabilities':
        from aegiscae.interfaces.codex_sessions import capability_map
        value = capability_map()
    else:
        from aegiscae.research.project import open_existing_readonly
        from aegiscae.research.scoped_sessions import SessionHub, load_roles
        roles = load_roles(Path(__file__).resolve().parents[1] / 'agents')
        value = SessionHub(open_existing_readonly(args.project), roles).inspect()
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    main()
