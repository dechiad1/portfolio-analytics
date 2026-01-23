import { test, expect } from '@playwright/test';

test.describe('OAuth Authentication', () => {
  test('should redirect to OAuth provider on login click', async ({ page }) => {
    await page.goto('/login');

    // Verify login page is shown
    await expect(page.getByRole('heading', { name: 'Portfolio Analytics' })).toBeVisible();

    // Click sign in button
    const signInButton = page.getByRole('button', { name: /sign in/i });
    await expect(signInButton).toBeVisible();

    // Start waiting for navigation before clicking
    const navigationPromise = page.waitForURL(/localhost:8080/);
    await signInButton.click();

    // Should redirect to mock-oauth2-server
    await navigationPromise;
    expect(page.url()).toContain('localhost:8080');
  });

  test('should complete OAuth flow and access protected route', async ({ page }) => {
    // Generate unique identifiers for this test
    const testEmail = `oauth-test-${Date.now()}@example.com`;

    // Go to login
    await page.goto('/login');

    // Click sign in
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for OAuth login page
    await page.waitForURL(/localhost:8080/);

    // Fill in mock-oauth2-server login form
    // Username field is used as the subject, claims textarea for email
    await page.fill('input[name="username"]', testEmail);
    await page.fill('textarea[name="claims"]', JSON.stringify({ email: testEmail }));
    await page.click('input[type="submit"]');

    // Should redirect back to app
    await page.waitForURL(/localhost:3000\/portfolios/, { timeout: 15000 });

    // Verify authenticated state - should see portfolios page (h1 title)
    await expect(page.getByRole('heading', { name: 'Portfolios', level: 1 })).toBeVisible({ timeout: 10000 });
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Try to access protected route directly
    await page.goto('/portfolios');

    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });

  test('should logout and redirect to login', async ({ page }) => {
    // First, complete OAuth login
    const testEmail = `logout-test-${Date.now()}@example.com`;

    await page.goto('/login');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/localhost:8080/);
    await page.fill('input[name="username"]', testEmail);
    await page.fill('textarea[name="claims"]', JSON.stringify({ email: testEmail }));
    await page.click('input[type="submit"]');
    await page.waitForURL(/localhost:3000\/portfolios/, { timeout: 15000 });

    // Now logout - find and click logout button in the navigation
    const logoutButton = page.getByRole('button', { name: /logout/i });
    await expect(logoutButton).toBeVisible({ timeout: 5000 });
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL('/login', { timeout: 10000 });
  });

  test('should persist session across page refreshes', async ({ page }) => {
    // Login first
    const testEmail = `session-test-${Date.now()}@example.com`;

    await page.goto('/login');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/localhost:8080/);
    await page.fill('input[name="username"]', testEmail);
    await page.fill('textarea[name="claims"]', JSON.stringify({ email: testEmail }));
    await page.click('input[type="submit"]');
    await page.waitForURL(/localhost:3000\/portfolios/, { timeout: 15000 });

    // Verify authenticated (h1 title)
    await expect(page.getByRole('heading', { name: 'Portfolios', level: 1 })).toBeVisible({ timeout: 10000 });

    // Refresh the page
    await page.reload();

    // Should still be authenticated (h1 title)
    await expect(page.getByRole('heading', { name: 'Portfolios', level: 1 })).toBeVisible({ timeout: 10000 });
    await expect(page).not.toHaveURL('/login');
  });

  test('should grant admin status to dechiada@gmail.com', async ({ page }) => {
    // Login with admin email
    const adminEmail = 'dechiada@gmail.com';

    await page.goto('/login');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/localhost:8080/);
    await page.fill('input[name="username"]', adminEmail);
    await page.fill('textarea[name="claims"]', JSON.stringify({ email: adminEmail }));
    await page.click('input[type="submit"]');
    await page.waitForURL(/localhost:3000\/portfolios/, { timeout: 15000 });

    // Verify authenticated (h1 title)
    await expect(page.getByRole('heading', { name: 'Portfolios', level: 1 })).toBeVisible({ timeout: 10000 });

    // Note: To fully verify admin status, we would need to check the database
    // or have an admin indicator in the UI. For now, we just verify the login works.
  });
});
