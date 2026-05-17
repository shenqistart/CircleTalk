import type { ZpaySignableParams } from "./signing";

export function renderZpayCheckoutHtml({
  submitUrl,
  params,
}: {
  submitUrl: string;
  params: ZpaySignableParams;
}): string {
  const hiddenInputs = Object.entries(params)
    .map(
      ([name, value]) =>
        `<input type="hidden" name="${escapeHtml(name)}" value="${escapeHtml(
          String(value),
        )}" />`,
    )
    .join("\n");

  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Redirecting to Alipay</title>
  </head>
  <body>
    <form id="zpay-checkout" method="post" action="${escapeHtml(submitUrl)}">
      ${hiddenInputs}
      <noscript>
        <button type="submit">Continue to Alipay</button>
      </noscript>
    </form>
    <script>
      document.getElementById("zpay-checkout").submit();
    </script>
  </body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
