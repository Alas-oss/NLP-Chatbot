import argparse

from crawler.config import ConfigError, load_config
from crawler.fetcher import Crawler, CrawlerDisabled


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="sources.yaml")
    parser.add_argument("--plan", action="store_true", help="Show what would be fetched, without fetching it")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}")
        raise SystemExit(1)

    crawler = Crawler(config)
    try:
        if args.plan:
            report = crawler.plan()
            print(f"Would fetch {len(report.would_fetch)} page(s):")
            for url in report.would_fetch:
                print(f"  FETCH   {url}")
            for url, reason in report.skipped.items():
                print(f"  SKIP    {url}  ({reason})")
        else:
            print("Nothing to do: pass --plan to see what the crawler would fetch.")
    except CrawlerDisabled as e:
        print(f"Crawler is disabled: {e}")
        raise SystemExit(1)
    finally:
        crawler.close()


if __name__ == "__main__":
    main()