import { test, expect } from '@playwright/test';

// Run tests serially to share authentication state
test.describe.configure({ mode: 'serial' });

test.describe('Portfolio Management', () => {
  // Generate unique email for the entire test suite
  const testUser = {
    email: `e2e-test-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
    password: 'TestPassword123',
  };

  test('should register and create a portfolio', async ({ page }) => {
    // Register a new user
    await page.goto('/register');
    await page.getByRole('textbox', { name: 'Email' }).fill(testUser.email);
    await page.getByRole('textbox', { name: 'Password', exact: true }).fill(testUser.password);
    await page.getByRole('textbox', { name: 'Confirm Password' }).fill(testUser.password);
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for redirect to portfolios page
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

  test('should add stock, fund, and treasury to portfolio and display holdings', async ({ page }) => {
    // Register a fresh user for this test
    const holdingsTestUser = {
      email: `e2e-holdings-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
      password: 'TestPassword123',
    };

    await page.goto('/register');
    await page.getByRole('textbox', { name: 'Email' }).fill(holdingsTestUser.email);
    await page.getByRole('textbox', { name: 'Password', exact: true }).fill(holdingsTestUser.password);
    await page.getByRole('textbox', { name: 'Confirm Password' }).fill(holdingsTestUser.password);
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for redirect to portfolios page
    await expect(page).toHaveURL('/portfolios', { timeout: 10000 });

    // Create a new portfolio for this test
    await page.getByRole('button', { name: 'New Portfolio' }).click();
    await page.getByRole('textbox', { name: 'Name' }).fill('Holdings Test Portfolio');
    await page.getByRole('dialog').getByRole('button', { name: 'Create Portfolio' }).click();

    // Wait for dialog to close
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Navigate to the portfolio detail page - look for card with both name and user email
    const portfolioCard = page.locator('a').filter({ hasText: 'Holdings Test Portfolio' }).filter({ hasText: holdingsTestUser.email });
    await portfolioCard.click();
    await expect(page.getByRole('heading', { name: 'Holdings Test Portfolio', level: 1 })).toBeVisible({ timeout: 10000 });

    // Helper function to add a holding
    async function addHolding(holding: {
      ticker: string;
      name: string;
      assetType: string;
      assetClass: string;
      sector: string;
      broker: string;
      quantity: string;
      purchaseDate: string;
      purchasePrice: string;
      currentPrice: string;
    }) {
      await page.getByRole('button', { name: 'Add Holding' }).click();
      await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });

      await page.locator('#ticker').fill(holding.ticker);
      await page.locator('#name').fill(holding.name);
      await page.locator('#assetType').selectOption(holding.assetType);
      await page.locator('#assetClass').selectOption(holding.assetClass);
      await page.locator('#sector').selectOption(holding.sector);
      await page.locator('#broker').fill(holding.broker);
      await page.locator('#quantity').fill(holding.quantity);
      await page.locator('#purchaseDate').fill(holding.purchaseDate);
      await page.locator('#purchasePrice').fill(holding.purchasePrice);
      await page.locator('#currentPrice').fill(holding.currentPrice);

      await page.getByRole('dialog').getByRole('button', { name: 'Add Holding' }).click();

      // Wait for dialog to close
      await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
    }

    // Add a Stock (AAPL)
    await addHolding({
      ticker: 'AAPL',
      name: 'Apple Inc.',
      assetType: 'Stock',
      assetClass: 'U.S. Stocks',
      sector: 'Technology',
      broker: 'Fidelity',
      quantity: '10',
      purchaseDate: '2024-01-15',
      purchasePrice: '185.00',
      currentPrice: '195.00',
    });
    await expect(page.getByText('AAPL')).toBeVisible();

    // Add a Mutual Fund (VTSAX)
    await addHolding({
      ticker: 'VTSAX',
      name: 'Vanguard Total Stock Market Index Fund',
      assetType: 'Mutual Fund',
      assetClass: 'U.S. Stocks',
      sector: 'Broad Market',
      broker: 'Vanguard',
      quantity: '50',
      purchaseDate: '2024-02-01',
      purchasePrice: '110.00',
      currentPrice: '115.00',
    });
    await expect(page.getByText('VTSAX')).toBeVisible();

    // Add a Treasury/Bond (SHY)
    await addHolding({
      ticker: 'SHY',
      name: 'iShares 1-3 Year Treasury Bond ETF',
      assetType: 'Bond',
      assetClass: 'Bonds',
      sector: 'Broad Market',
      broker: 'Schwab',
      quantity: '100',
      purchaseDate: '2024-03-01',
      purchasePrice: '82.00',
      currentPrice: '82.50',
    });
    await expect(page.getByText('SHY')).toBeVisible();

    // Verify all three holdings are displayed
    await expect(page.getByText('AAPL')).toBeVisible();
    await expect(page.getByText('VTSAX')).toBeVisible();
    await expect(page.getByText('SHY')).toBeVisible();
  });

  test('should autofill form fields when selecting ticker from search results', async ({ page }) => {
    // Register a fresh user for this test
    const autofillTestUser = {
      email: `e2e-autofill-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
      password: 'TestPassword123',
    };

    await page.goto('/register');
    await page.getByRole('textbox', { name: 'Email' }).fill(autofillTestUser.email);
    await page.getByRole('textbox', { name: 'Password', exact: true }).fill(autofillTestUser.password);
    await page.getByRole('textbox', { name: 'Confirm Password' }).fill(autofillTestUser.password);
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Wait for redirect to portfolios page
    await expect(page).toHaveURL('/portfolios', { timeout: 10000 });

    // Create a portfolio first
    await page.getByRole('button', { name: 'New Portfolio' }).click();
    await page.getByRole('textbox', { name: 'Name' }).fill('Autofill Test Portfolio');
    await page.getByRole('dialog').getByRole('button', { name: 'Create Portfolio' }).click();

    // Wait for dialog to close
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });

    // Navigate to the portfolio detail page
    const portfolioCard = page.locator('a').filter({ hasText: 'Autofill Test Portfolio' }).filter({ hasText: autofillTestUser.email });
    await portfolioCard.click();
    await expect(page.getByRole('heading', { name: 'Autofill Test Portfolio', level: 1 })).toBeVisible({ timeout: 10000 });

    // Click "Add Holding" to show the modal
    await page.getByRole('button', { name: 'Add Holding' }).click();
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });

    // Type in the ticker search field to trigger search (VFIAX is in the DuckDB database)
    const tickerInput = page.locator('#ticker');
    await tickerInput.fill('VFIAX');

    // Wait for search results dropdown to appear
    await expect(page.getByText('Vanguard 500 Index Fund')).toBeVisible({ timeout: 10000 });

    // Click on the VFIAX result
    await page.getByText('Vanguard 500 Index Fund').click();

    // Verify that form fields were autofilled
    const nameInput = page.locator('#name');
    await expect(nameInput).toHaveValue('Vanguard 500 Index Fund');

    const assetClassSelect = page.locator('#assetClass');
    await expect(assetClassSelect).toHaveValue('U.S. Stocks');

    // The ticker should now be VFIAX
    await expect(tickerInput).toHaveValue('VFIAX');
  });
});
