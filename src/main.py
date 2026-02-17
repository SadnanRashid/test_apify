import asyncio
import zendriver as zd
import logging

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

num_pages = 4


async def get_page_cids(url, max_retries=3):
    """
    Opens its OWN browser instance to avoid ConcurrencyErrors.
    """
    logger.info(f"Starting browser for: {url}")
    browser = await zd.start(headless=True)

    try:
        for attempt in range(1, max_retries + 1):
            try:
                page = await browser.get(url)

                await asyncio.sleep(3)

                await page.wait_for(".VkpGBb", timeout=5)
                cards = await page.query_selector_all(".VkpGBb")

                if len(cards) < 5:
                    raise ValueError(f"Low result count ({len(cards)})")

                page_data = []
                for card in cards:
                    link_element = await card.query_selector("a[data-cid]")
                    if link_element:
                        cid = link_element.attrs.get("data-cid")
                        name_el = await card.query_selector(".OSrXXb")
                        name = name_el.text if name_el else "Unknown"
                        if cid:
                            page_data.append({"name": name, "cid": cid})

                logger.info(f"Successfully scraped {len(page_data)} CIDs from {url}")
                return page_data

            except Exception as e:
                # Log as a soft error (warning)
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {url}: {e}")
                if attempt == max_retries:
                    logger.error(
                        f"Failed to scrape {url} after {max_retries} attempts."
                    )
                    return []
                await asyncio.sleep(3)
        return []
    finally:
        await browser.stop()
        logger.debug(f"Browser closed for {url}")


async def main():
    """
    Main orchestrator.
    """
    semaphore = asyncio.Semaphore(2)
    base_url = "https://www.google.com/search?tbm=lcl&q=spa+in+new+york&hl=en"

    urls = [f"{base_url}&start={i * 20}" for i in range(num_pages)]
    logger.info(
        f"Initialization complete. Preparing to scrape {len(urls)} pages with concurrency of 2."
    )

    async def sem_task(url):
        async with semaphore:
            return await get_page_cids(url)

    try:
        tasks = [sem_task(url) for url in urls]
        results = await asyncio.gather(*tasks)

        # Flatten results
        final_list = [item for sublist in results for item in sublist]

        # Deduplicate
        seen_cids = set()
        unique_list = []
        for entry in final_list:
            if entry["cid"] not in seen_cids:
                unique_list.append(entry)
                seen_cids.add(entry["cid"])

        logger.info("Scraping finished. Processing results...")

        print("\n" + "=" * 30)
        print("        FINAL RESULTS")
        print("=" * 30)
        for entry in unique_list:
            print(f"{entry['name']}: {entry['cid']}")

        logger.info(f"Collection complete. Total unique CIDs: {len(unique_list)}")
        return unique_list

    except Exception as e:
        logger.critical(f"Global execution error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
