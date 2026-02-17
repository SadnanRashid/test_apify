import asyncio
import zendriver as zd


num_pages = 5


async def get_page_cids(url, max_retries=3):
    """
    Opens its OWN browser instance to avoid ConcurrencyErrors.
    """
    browser = await zd.start(headless=True)

    try:
        for attempt in range(1, max_retries + 1):
            try:
                page = await browser.get(url)

                try:
                    await page.wait_for_idle()
                except:
                    await asyncio.sleep(2)

                await page.wait_for(".VkpGBb", timeout=10)
                cards = await page.query_selector_all(".VkpGBb")

                if len(cards) < 5:
                    raise ValueError(f"Only found {len(cards)} results. Retrying...")

                page_data = []
                for card in cards:
                    link_element = await card.query_selector("a[data-cid]")
                    if link_element:
                        cid = link_element.attrs.get("data-cid")
                        name_el = await card.query_selector(".OSrXXb")
                        name = name_el.text if name_el else "Unknown"
                        if cid:
                            page_data.append({"name": name, "cid": cid})

                print(f"Successfully scraped {len(page_data)} CIDs from {url}")
                return page_data

            except Exception as e:
                print(f"Attempt {attempt} failed for {url}: {e}")
                if attempt == max_retries:
                    return []
                await asyncio.sleep(3)
        return []
    finally:
        await browser.stop()


async def main():
    """
    Main orchestrator.
    """
    semaphore = asyncio.Semaphore(2)

    base_url = "https://www.google.com/search?tbm=lcl&q=spa+in+new+york&hl=en"

    # Generate URLs based on the dynamic num_pages input
    urls = [f"{base_url}&start={i * 20}" for i in range(num_pages)]
    print(f"Prepared {len(urls)} URLs to scrape. URLs: {urls}")

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

        print("\n--- Final Results ---")
        for entry in unique_list:
            print(f"{entry['name']}: {entry['cid']}")

        print(f"\nTotal unique CIDs collected: {len(unique_list)}")
        return unique_list

    except Exception as e:
        print(f"Global error: {e}")


if __name__ == "__main__":
    # CHANGE THIS NUMBER TO CONTROL THE PAGES
    asyncio.run(main())
