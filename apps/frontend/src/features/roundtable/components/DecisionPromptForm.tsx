import { useState } from 'react'

export function DecisionPromptForm({ onSubmit, disabled }: { onSubmit: (prompt: string) => void; disabled?: boolean }) {
  const [prompt, setPrompt] = useState('')
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        if (prompt.trim()) onSubmit(prompt.trim())
      }}
      className="rounded-2xl border bg-white p-5 shadow-sm"
    >
      <label className="block text-sm font-semibold text-gray-700">决策题</label>
      <textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        rows={4}
        className="mt-2 w-full rounded-xl border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-gray-900/10"
        placeholder="例如：我是否应该在今年离开大厂去做 AI 创业？"
      />
      <button disabled={disabled || !prompt.trim()} className="mt-3 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
        创建圆桌会话
      </button>
    </form>
  )
}
