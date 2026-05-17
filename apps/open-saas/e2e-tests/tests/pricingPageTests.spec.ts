import { expect, test } from "@playwright/test";

test.describe("pricing page tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/pricing");
  });

  test("shows Circle pricing copy and plans", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Buy Circle credits" }),
    ).toBeVisible();
    await expect(page.getByText("Purchase credits with Alipay")).toBeVisible();
    await expect(page.getByText("Starter")).toHaveCount(0);
    await expect(page.getByText("Pro")).toHaveCount(0);
    await expect(page.getByText("10 Credits")).toBeVisible();
    await expect(page.getByText("¥9.90")).toBeVisible();
  });

  test("logged out user can buy credits by logging in", async ({ page }) => {
    const chooseButton = page.getByRole("button", {
      name: "Log in to buy credits",
    });

    await expect(chooseButton).toBeVisible();
    await expect(chooseButton).toBeEnabled();
    await chooseButton.click();

    await page.waitForURL("**/login");
    await expect(page.getByText("Circle Roundtable")).toBeVisible();
  });

  test("does not show payment-provider starter instructions", async ({
    page,
  }) => {
    await expect(page.getByText("Choose between Stripe")).toHaveCount(0);
    await expect(page.getByText("test credit card")).toHaveCount(0);
    await expect(page.getByText("LemonSqueezy")).toHaveCount(0);
    await expect(page.getByText("Polar")).toHaveCount(0);
  });
});
