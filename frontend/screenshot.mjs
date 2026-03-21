import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const outDir = '/Users/chenjianfeng/SAAS/manual_images';
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    console.log("Navigating to login...");
    await page.goto('http://localhost/login');

    console.log("Logging in...");
    await page.fill('input[type="text"]', 'chenjf79');
    await page.fill('input[type="password"]', 'chenjf8018');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForTimeout(3000); // let animations settle
    await page.screenshot({ path: path.join(outDir, '01_dashboard.png') });
    console.log("Dashboard captured");

    // Projects List
    await page.click('text=项目管理');
    await page.waitForTimeout(2000);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(outDir, '02_projects_list.png') });
    console.log("Projects list captured");

    // Project Detail
    const firstProject = await page.$('.ant-table-row a');
    if (firstProject) {
        await firstProject.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: path.join(outDir, '03_project_detail.png'), fullPage: true });
        console.log("Project detail captured");

        // Click pre review
        const preReviewBtn = await page.$('button:has-text("智能预审")');
        if (preReviewBtn) {
            // await preReviewBtn.click();
            // await page.waitForTimeout(5000);
            // await page.screenshot({ path: path.join(outDir, '03a_project_detail_after_ai.png'), fullPage: true });
        }
    }

    // Entities
    await page.click('text=主体管理');
    await page.waitForTimeout(500);
    await page.click('text=境内主体');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(outDir, '04_domestic_entities.png') });
    console.log("Domestic entities captured");

    await page.click('text=境外标的');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(outDir, '05_overseas_entities.png') });
    console.log("Overseas entities captured");

    // AI Reports
    await page.click('text=AI 报告');
    await page.waitForTimeout(1000);

    // click project select
    const select = await page.$('.ant-select-selector');
    if (select) {
        await select.click();
        await page.waitForTimeout(500);
        await page.click('.ant-select-item-option');
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(outDir, '06_ai_reports.png') });
        console.log("AI reports captured");
    }

    // System Config
    await page.click('text=规则管理');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(outDir, '07_rules.png') });

    await page.click('text=系统配置');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(outDir, '08_system_config.png') });

    await browser.close();
    console.log("Done!");
})();
