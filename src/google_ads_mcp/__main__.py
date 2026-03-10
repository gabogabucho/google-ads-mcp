"""Entry point: python -m google_ads_mcp"""

from .server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
