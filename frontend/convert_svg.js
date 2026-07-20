import { chromium } from 'playwright';
import path from 'path';

(async () => {
    console.log('Starting Playwright for SVG...');
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
    
    // Create an HTML snippet that embeds the SVG
    await page.setContent(`
        <html>
        <body style="margin: 0; display: flex; justify-content: center; align-items: center; background: white; height: 100vh;">
            <img src="file:///C:/Users/Archi%20Thakkar/Downloads/supply_chain_predictor_use_case_diagram.svg" style="max-width: 100%; max-height: 100%;" />
        </body>
        </html>
    `, { waitUntil: 'networkidle' });
    
    await page.waitForTimeout(2000); // Give image time to render
    
    await page.screenshot({ path: 'C:/Users/Archi Thakkar/Downloads/use_case_diagram.png', fullPage: true });

    await browser.close();
    console.log('Saved SVG to PNG successfully.');
})();
