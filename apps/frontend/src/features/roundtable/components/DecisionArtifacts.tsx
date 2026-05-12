import type { DecisionArtifact } from '@/features/roundtable/types'

interface DecisionArtifactsProps {
  artifact?: DecisionArtifact
}

export function DecisionArtifacts({ artifact }: DecisionArtifactsProps) {
  if (!artifact) {
    return (
      <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-500">
        三件套将在圆桌流完成后从数据库恢复显示。
      </section>
    )
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-semibold text-blue-700">Step 4 · 三件套</p>
      <div className="mt-3 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-4">
          <h3 className="font-semibold text-slate-950">Memo</h3>
          <p className="mt-2 text-sm leading-6 text-slate-700">{artifact.memo}</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-4">
          <h3 className="font-semibold text-slate-950">Recommendation</h3>
          <p className="mt-2 text-sm leading-6 text-slate-700">{artifact.recommendation}</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-4">
          <h3 className="font-semibold text-slate-950">Reasons</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {artifact.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="mt-4 rounded-xl bg-slate-50 p-4">
        <h3 className="font-semibold text-slate-950">Debate map</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {artifact.debateMap.map((item) => (
            <div className="rounded-lg bg-white p-3 text-sm" key={`${item.personaName}-${item.position}`}>
              <p className="font-medium text-slate-950">{item.personaName}</p>
              <p className="mt-1 text-slate-700">{item.position}</p>
              <p className="mt-1 text-xs text-slate-500">{item.keyConcern}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
