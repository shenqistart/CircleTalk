export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-foreground text-4xl font-bold">Privacy Policy</h1>
      <div className="text-muted-foreground mt-8 space-y-5 leading-7">
        <p>
          CircleTalk stores account, billing, and roundtable session data needed
          to provide the service. Roundtable prompts, transcripts, artifacts,
          usage records, and credit activity are scoped to the signed-in user.
        </p>
        <p>
          Google OAuth is used for authentication. Stripe is used for payment
          processing. The private AI Worker receives only authorized roundtable
          generation requests from the CircleTalk server.
        </p>
        <p>
          Production operators should configure retention, support contact, and
          any region-specific legal language before public launch.
        </p>
      </div>
    </main>
  );
}
