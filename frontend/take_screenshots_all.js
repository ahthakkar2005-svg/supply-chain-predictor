import { chromium } from 'playwright';

(async () => {
    console.log('Starting Playwright...');
    const browser = await chromium.launch();
    
    // Desktop View
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000); // Give it time to load map and data

    const pages = ['Dashboard', 'Predictions', 'Alerts', 'Suppliers', 'Ports', 'Analytics', 'Settings'];

    for (const pageName of pages) {
        console.log(`Navigating to ${pageName}...`);
        await page.click(`text="${pageName}"`);
        await page.waitForTimeout(1500); // Wait for animations and data
        const filename = pageName.toLowerCase() + '.png';
        await page.screenshot({ path: '../' + filename });
        console.log(`Saved ${filename}`);
    }

    await page.close();
    await browser.close();
    console.log('Done.');
})();
