import { chromium } from 'playwright';

(async () => {
    console.log('Starting Playwright...');
    const browser = await chromium.launch();
    
    // Desktop View
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000); // Give it time to load map and data
    await page.screenshot({ path: '../dashboard.png' });
    console.log('Saved dashboard.png');
    await page.close();

    // Mobile View
    const mobilePage = await browser.newPage({ viewport: { width: 375, height: 667 } });
    await mobilePage.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    await mobilePage.waitForTimeout(3000); // Give it time to load map and data
    await mobilePage.screenshot({ path: '../dashboard_mobile.png' });
    console.log('Saved dashboard_mobile.png');
    await mobilePage.close();

    await browser.close();
    console.log('Done.');
})();
