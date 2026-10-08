import { chromium } from "playwright-core";

const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
const base = "http://127.0.0.1:5174";

async function ask(message) {
  await page.locator(".chat-toggle").click();
  await page.getByPlaceholder("Ask about our products…").fill(message);
  await page.getByRole("button", { name: "Send message" }).click();
  await page.locator(".typing").waitFor({ state: "visible" });
  await page.locator(".typing").waitFor({ state: "detached", timeout: 120_000 });
}

await page.goto(`${base}/products/baseball-left-chest-crewneck`, { waitUntil: "networkidle" });
await ask("What is the price of this crewneck, and how many are left in size L?");
await page.locator(".assistant-message").filter({ hasText: "$58.00" }).waitFor({ timeout: 10_000 });
await page.evaluate(() => window.scrollTo(0, 0));
await page.waitForTimeout(800);
await page.screenshot({ path: "../output/app_check_images/inventory.png" });
const inventoryText = await page.locator(".assistant-message").last().innerText();

await page.goto(`${base}/products`, { waitUntil: "networkidle" });
await ask("What hoodies do you have?");
await page.locator(".chat-results-section .product-card").first().waitFor({ timeout: 120_000 });
const cards = await page.locator(".chat-results-section .product-card").count();
const names = await page.locator(".chat-results-section .product-card h2").allInnerTexts();
const hrefs = await page.locator(".chat-results-section .product-card").evaluateAll((links) => links.map((link) => link.getAttribute("href")));
await page.locator(".chat-results-section").evaluate((section) => window.scrollTo(0, section.getBoundingClientRect().top + window.scrollY - 110));
await page.waitForTimeout(800);
await page.screenshot({ path: "../output/app_check_images/chat-search.png" });

await page.goto(`${base}/products`, { waitUntil: "networkidle" });
await page.getByPlaceholder("Search the collection").fill("zzzz-no-match");
await page.getByText("No matching products found.").waitFor();
await page.screenshot({ path: "../output/app_check_images/usability.png", fullPage: true });
const emptyState = await page.getByText("No matching products found.").isVisible();
const clearFilters = await page.getByText("Clear filters").isVisible();

console.log(JSON.stringify({ inventoryText, cards, names, hrefs, emptyState, clearFilters }, null, 2));
await browser.close();
