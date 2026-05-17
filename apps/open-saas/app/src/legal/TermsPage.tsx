export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-foreground text-4xl font-bold">Terms of Service</h1>
      <div className="text-muted-foreground mt-8 space-y-5 leading-7">
        <p>
          CircleTalk provides AI-assisted roundtable discussions for decision
          support. Generated output should be reviewed by users before acting on
          legal, financial, medical, hiring, or other high-stakes decisions.
        </p>
        <p>
          Credits and subscriptions are processed through Stripe. Credits are
          deducted according to the product rules shown at checkout and in the
          app.
        </p>
        <p>
          Production operators should replace this starter text with final legal
          terms, refund language, support contact, and jurisdiction-specific
          requirements before public launch.
        </p>
      </div>
    </main>
  );
}
