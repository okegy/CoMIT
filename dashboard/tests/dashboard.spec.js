import { test, expect } from '@playwright/test';

test.describe('CoMIT Dashboard End-to-End Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Assuming the Vite server is running on port 5175
    await page.goto('http://localhost:5175');
  });

  test('should load the dashboard and verify title', async ({ page }) => {
    await expect(page).toHaveTitle(/Vite \+ React/);
    await expect(page.locator('text=CoMIT')).toBeVisible();
    await expect(page.locator('text=Command Center').first()).toBeVisible();
  });

  test('should switch to Admin Portal tab', async ({ page }) => {
    // Click the Admin Portal tab
    await page.click('button:has-text("Admin Portal")');
    // Verify the Admin feed is visible
    await expect(page.locator('text=Live Enforcement Feed')).toBeVisible();
    await expect(page.locator('text=Evidentiary Review')).toBeVisible();
  });

  test('should trigger emergency ping and display V2V broadcast', async ({ page }) => {
    // Ensure we are on Command Center
    await page.click('button:has-text("Command Center")');
    
    // Click the Emergency Ping button
    await page.click('button:has-text("Trigger emergency ping")');
    
    // Verify that the emergency banner appears (simulating MQTT event receipt)
    // The exact banner text depends on the mock, but the events log should show it
    await expect(page.locator('text=priority ping sent')).toBeVisible();
  });

  test('should switch language to French', async ({ page }) => {
    await page.click('button:has-text("fr")');
    // 'Command Center' becomes 'Centre de cde'
    await expect(page.locator('text=Centre de cde')).toBeVisible();
  });
});
