import json

from backend.db import connect, get_database, initialize_database


def main():
    with connect() as client:
        summary = initialize_database(get_database(client))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
