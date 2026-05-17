import { expect, test } from "@playwright/test";

test.describe("roundtable access tests", () => {
  test("roundtable is protected for logged out users", async ({ page }) => {
    await page.goto("/roundtable");

    await page.waitForURL("**/login");
    await expect(page.getByText("Circle Roundtable")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Log in to your account" })).toBeVisible();
  });

  test("login page exposes the Google provider", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByText("Circle Roundtable")).toBeVisible();
    await expect(page.locator('a[href="http://localhost:3001/auth/google/login"]')).toHaveCount(1);
    await expect(page.locator('a[href="http://localhost:3001/auth/google/login"]')).toHaveAttribute(
      "href",
      "http://localhost:3001/auth/google/login",
    );
  });
});
