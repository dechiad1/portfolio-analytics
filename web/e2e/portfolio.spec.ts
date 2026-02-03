import { test, expect, type Page } from '@playwright/test';

// Run tests serially to share authentication state
test.describe.configure({ mode: 'serial' });

/**
 * Helper function to perform OAuth login via mock-oauth2-server.
 */
async function oauthLogin(page: Page, email: string) {
  await page.goto('/login');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/localhost:8080/);
  await page.fill('input[name="username"]', email);
  await page.fill('textarea[name="claims"]', JSON.stringify({ email }));
  await page.click('input[type="submit"]');
  await page.waitForURL(/\/portfolios/, { timeout: 15000 });
}

test.describe('Portfolio Management', () => {
  // Generate unique email for the entire test suite
  const testUser = {
    email: `e2e-test-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
  };

  test('should login via OAuth and create a portfolio', async ({ page }) => {
    // Login via OAuth
    await oauthLogin(page, testUser.email);

    // Wait for portfolios page
    await expect(page).toHaveURL('/portfolios', { timeout: 10000 });

    // Click "New Portfolio" button
    await page.getByRole('button', { name: 'New Portfolio' }).click();

    // Fill in portfolio name
    await page.getByRole('textbox', { name: 'Name' }).fill('E2E Test Portfolio');

    // Submit the form
    await page.getByRole('dialog').getByRole('button', { name: 'Create Portfolio' }).click();

    // Verify portfolio was created - look for card with both name and user email
    const portfolioCard = page.locator('a').filter({ hasText: 'E2E Test Portfolio' }).filter({ hasText: testUser.email });
    await expect(portfolioCard).toBeVisible({ timeout: 10000 });
  });

  test('should add positions to portfolio and display them', async ({ page }) => {
    // Login with a fresh user for this test
    const positionsTestUser = {
      email: `e2e-positions-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
    };

    await oauthLogin(page, positionsTestUser.email);

    // Wait for portfolios page
    await expect(page).toHaveURL('/portfolios', { timeout: 10000 });

    // Create a new portfolio for this test
    await page.getByRole('button', { name: 'New Portfolio' }).click();
    await page.getByRole('textbox', { name: 'Name' }).fill('Positions Test Portfolio');
    await page.getByRole('dialog').getByRole('button', { name: 'Create Portfolio' }).click();

    // Wait for dialog to close
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Navigate to the portfolio detail page - click on the portfolio card
    const portfolioCard = page.locator('a').filter({ hasText: 'Positions Test Portfolio' });
    await portfolioCard.click();
    await expect(page.getByRole('heading', { name: 'Positions Test Portfolio', level: 1 })).toBeVisible({ timeout: 10000 });

    // Helper function to add a position
    async function addPosition(position: {
      ticker: string;
      quantity: string;
      price: string;
      eventDate: string;
    }) {
      await page.getByRole('button', { name: 'Add Position' }).click();
      await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });

      await page.locator('#ticker').fill(position.ticker);
      await page.locator('#quantity').fill(position.quantity);
      await page.locator('#price').fill(position.price);
      await page.locator('#eventDate').fill(position.eventDate);

      await page.getByRole('dialog').getByRole('button', { name: 'Add Position' }).click();

      // Wait for dialog to close
      await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
    }

    // Add a Stock (AAPL)
    await addPosition({
      ticker: 'AAPL',
      quantity: '10',
      price: '185.00',
      eventDate: '2024-01-15',
    });
    await expect(page.getByRole('cell', { name: 'AAPL', exact: true })).toBeVisible();

    // Add another Stock (MSFT)
    await addPosition({
      ticker: 'MSFT',
      quantity: '50',
      price: '380.00',
      eventDate: '2024-02-01',
    });
    await expect(page.getByRole('cell', { name: 'MSFT', exact: true })).toBeVisible();

    // Verify both positions are displayed in the table
    await expect(page.getByRole('cell', { name: 'AAPL', exact: true })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'MSFT', exact: true })).toBeVisible();
    await expect(page.getByText('Apple Inc.')).toBeVisible();
    await expect(page.getByText('Microsoft Corporation')).toBeVisible();
  });

  test('should autofill price when selecting ticker from search results', async ({ page }) => {
    // Login with a fresh user for this test
    const autofillTestUser = {
      email: `e2e-autofill-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
    };

    await oauthLogin(page, autofillTestUser.email);

    // Wait for portfolios page
    await expect(page).toHaveURL('/portfolios', { timeout: 10000 });

    // Create a portfolio first
    await page.getByRole('button', { name: 'New Portfolio' }).click();
    await page.getByRole('textbox', { name: 'Name' }).fill('Autofill Test Portfolio');
    await page.getByRole('dialog').getByRole('button', { name: 'Create Portfolio' }).click();

    // Wait for dialog to close
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Navigate to the portfolio detail page
    const portfolioCard = page.locator('a').filter({ hasText: 'Autofill Test Portfolio' });
    await portfolioCard.click();
    await expect(page.getByRole('heading', { name: 'Autofill Test Portfolio', level: 1 })).toBeVisible({ timeout: 10000 });

    // Click "Add Position" to show the modal
    await page.getByRole('button', { name: 'Add Position' }).click();
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });

    // Type in the ticker search field to trigger search (AAPL has price data)
    const tickerInput = page.locator('#ticker');
    await tickerInput.fill('AAPL');

    // Wait for search results dropdown to appear
    await expect(page.getByText('Apple Inc.')).toBeVisible({ timeout: 10000 });

    // Click on the AAPL result
    await page.getByText('Apple Inc.').click();

    // Verify that the ticker was selected
    await expect(tickerInput).toHaveValue('AAPL');

    // Verify that the price field was auto-populated (wait for async API call)
    const priceInput = page.locator('#price');
    await expect(priceInput).not.toHaveValue('', { timeout: 10000 });
  });

  // Skip: Risk analysis depends on LLM service which may be slow or unavailable in test env
  test.skip('should generate, view history, switch between, and delete risk analyses', async ({ page }) => {
    // Login with a fresh user for this test
    const riskTestUser = {
      email: `e2e-risk-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
    };

    await oauthLogin(page, riskTestUser.email);
    await expect(page).toHaveURL('/portfolios', { timeout: 10000 });

    // Create a portfolio first
    await page.getByRole('button', { name: 'New Portfolio' }).click();
    await page.getByRole('textbox', { name: 'Name' }).fill('Risk Analysis Test Portfolio');
    await page.getByRole('dialog').getByRole('button', { name: 'Create Portfolio' }).click();

    // Wait for portfolio card to appear (indicating creation success and modal close)
    const portfolioCard = page.locator('a').filter({ hasText: 'Risk Analysis Test Portfolio' });
    await expect(portfolioCard).toBeVisible({ timeout: 15000 });

    // Navigate to the portfolio detail page
    await portfolioCard.click();
    await expect(page.getByRole('heading', { name: 'Risk Analysis Test Portfolio', level: 1 })).toBeVisible({ timeout: 10000 });

    // Add a position first (required for risk analysis)
    await page.getByRole('button', { name: 'Add Position' }).click();
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });

    await page.locator('#ticker').fill('AAPL');
    await page.locator('#quantity').fill('10');
    await page.locator('#price').fill('185.00');
    await page.locator('#eventDate').fill('2024-01-15');
    await page.getByRole('dialog').getByRole('button', { name: 'Add Position' }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Scroll to risk analysis section
    const riskSection = page.locator('text=AI Risk Analysis').first();
    await riskSection.scrollIntoViewIfNeeded();

    // Check no history dropdown initially (no analyses exist yet)
    const historyDropdown = page.getByLabel('Select risk analysis');
    await expect(historyDropdown).not.toBeVisible();

    // Click generate analysis button
    await page.getByRole('button', { name: 'Generate Analysis' }).click();

    // Wait for analysis to be generated (indicated by results appearing)
    // Note: In mock/test environment, LLM returns immediately with fallback
    await expect(page.getByText(/Generated on/)).toBeVisible({ timeout: 30000 });

    // Now history dropdown should appear with one item
    await expect(historyDropdown).toBeVisible({ timeout: 5000 });

    // Generate a second analysis
    await page.getByRole('button', { name: 'New Analysis' }).click();
    await expect(page.getByText(/Generated on/)).toBeVisible({ timeout: 30000 });

    // History dropdown should now have multiple options
    const options = await historyDropdown.locator('option').count();
    expect(options).toBeGreaterThanOrEqual(2);

    // Get current option count before delete
    const optionCountBefore = await historyDropdown.locator('option').count();

    // Set up dialog handler before clicking delete
    page.once('dialog', dialog => dialog.accept());

    // Delete the current analysis
    await page.getByRole('button', { name: 'Delete analysis' }).click();

    // Wait for the option count to decrease (deterministic wait instead of timeout)
    await expect(historyDropdown.locator('option')).toHaveCount(optionCountBefore - 1, { timeout: 5000 });

    // After deletion, verify the history dropdown still exists (one analysis remains)
    await expect(historyDropdown).toBeVisible({ timeout: 5000 });
  });
});
