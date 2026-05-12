import { AI_SDK_TEXT_STREAM_PROTOCOL } from '@/features/roundtable/hooks/useRoundtableChat'

export function DeploymentStatusBanner() {
  return (
    <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
      <strong>专业栈首版：</strong>Vite/Vercel 前端 + FastAPI/Render 后端 + Render Postgres；前端显式使用 AI SDK Text Stream
      contract（streamProtocol: {AI_SDK_TEXT_STREAM_PROTOCOL}），结构化三件套以 completion 后 refetch 为准。
    </div>
  )
}
