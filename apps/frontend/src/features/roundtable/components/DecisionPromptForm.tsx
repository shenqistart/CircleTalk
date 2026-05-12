import { useState } from 'react'

interface DecisionPromptFormProps {
  isBusy: boolean
  onCreate: (decisionPrompt: string) => Promise<void>
  onRecommend: (decisionPrompt: string) => Promise<void>
}

export function DecisionPromptForm({ isBusy, onCreate, onRecommend }: DecisionPromptFormProps) {
  const [decisionPrompt, setDecisionPrompt] = useState('')
  const canSubmit = decisionPrompt.trim().length > 0 && !isBusy

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canSubmit) return
    void onCreate(decisionPrompt.trim())
  }

  return (
    <form className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <div className="mb-3">
        <p className="text-sm font-semibold text-blue-700">Step 1 · 决策题</p>
        <h2 className="text-xl font-bold text-slate-950">输入要被圆桌讨论的真实问题</h2>
      </div>
      <textarea
        className="min-h-32 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        placeholder="例如：我是否应该在今年把团队从外包交付转成自研产品？"
        value={decisionPrompt}
        onChange={(event) => setDecisionPrompt(event.target.value)}
      />
      <div className="mt-3 flex flex-wrap gap-3">
        <button
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={!canSubmit}
          type="button"
          onClick={() => void onRecommend(decisionPrompt.trim())}
        >
          推荐人物
        </button>
        <button
          className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
          disabled={!canSubmit}
          type="submit"
        >
          创建圆桌会话
        </button>
      </div>
    </form>
  )
}
