import { expect, test } from "@playwright/test";

test.describe("general landing page tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("has title", async ({ page }) => {
    await expect(page).toHaveTitle("Circle Roundtable");
  });

  test("start a Circle link opens login", async ({ page }) => {
    await page.getByRole("link", { name: "Start a Circle" }).click();
    await page.waitForURL("**/login");
  });

  test("headings", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Frequently asked questions" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Private AI roundtables for better decisions",
      }),
    ).toBeVisible();
  });

  test("does not show starter template copy", async ({ page }) => {
    await expect(page.getByText("Your SaaS")).toHaveCount(0);
    await expect(page.getByText("OpenSaaS")).toHaveCount(0);
    await expect(page.getByText("Some cool words")).toHaveCount(0);
  });
});

test.describe("cookie consent tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("cookie consent banner rejection does not set cc_cookie", async ({
    context,
    page,
  }) => {
    await page.$$('button:has-text("Reject all")');
    await page.click('button:has-text("Reject all")');

    const cookies = await context.cookies();
    const consentCookie = cookies.find((c) => c.name === "cc_cookie");
    const cookieObject = JSON.parse(decodeURIComponent(consentCookie.value));
    expect(cookieObject.categories.includes("analytics")).toBeFalsy();
  });

  test("cookie consent banner acceptance sets analytics consent", async ({
    context,
    page,
  }) => {
    await page.$$('button:has-text("Accept all")');
    await page.click('button:has-text("Accept all")');

    let cookies = await context.cookies();
    const consentCookie = cookies.find((c) => c.name === "cc_cookie");
    const cookieObject = JSON.parse(decodeURIComponent(consentCookie.value));
    expect(cookieObject.categories.includes("analytics")).toBeTruthy();
  });
});
