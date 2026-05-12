import type { DecisionArtifact } from '@/features/roundtable/types'

export function DecisionArtifacts({ artifact }: { artifact?: DecisionArtifact }) {
  if (!artifact) return null
  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <h2 className="font-semibold">决策三件套</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-gray-50 p-3"><div className="text-xs text-gray-400">Memo</div><p className="text-sm">{artifact.memo}</p></div>
        <div className="rounded-xl bg-gray-50 p-3"><div className="text-xs text-gray-400">Recommendation</div><p className="text-sm">{artifact.recommendation}</p></div>
      </div>
      <ul className="mt-3 list-disc pl-5 text-sm text-gray-700">{artifact.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
    </section>
  )
}
