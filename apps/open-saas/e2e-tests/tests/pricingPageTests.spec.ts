import { expect, test } from "@playwright/test";

test.describe("pricing page tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/pricing");
  });

  test("shows Circle pricing copy and plans", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Choose your Circle plan" }),
    ).toBeVisible();
    await expect(page.getByText("Subscribe for recurring Circle usage")).toBeVisible();
    await expect(page.getByText("Starter")).toBeVisible();
    await expect(page.getByText("Pro")).toBeVisible();
    await expect(page.getByText("10 Credits")).toBeVisible();
  });

  test("logged out user can choose a plan by logging in", async ({ page }) => {
    const chooseButton = page.getByRole("button", { name: "Log in to choose" }).first();

    await expect(chooseButton).toBeVisible();
    await expect(chooseButton).toBeEnabled();
    await chooseButton.click();

    await page.waitForURL("**/login");
    await expect(page.getByText("Circle Roundtable")).toBeVisible();
  });

  test("does not show payment-provider starter instructions", async ({ page }) => {
    await expect(page.getByText("Choose between Stripe")).toHaveCount(0);
    await expect(page.getByText("test credit card")).toHaveCount(0);
    await expect(page.getByText("LemonSqueezy")).toHaveCount(0);
    await expect(page.getByText("Polar")).toHaveCount(0);
  });
});
