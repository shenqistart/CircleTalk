import { Check, Circle, Lock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/shared/lib/utils'

export type RoundtableStepId = 'prompt' | 'personas' | 'discussion' | 'artifacts'

export interface RoundtableStep {
  id: RoundtableStepId
  isAvailable: boolean
  isComplete: boolean
}

interface RoundtableStepperProps {
  activeStep: RoundtableStepId
  steps: RoundtableStep[]
  onStepChange: (stepId: RoundtableStepId) => void
}

export function RoundtableStepper({ activeStep, onStepChange, steps }: RoundtableStepperProps) {
  const { t } = useTranslation()

  return (
    <nav aria-label={t('roundtable.stepper.label')} className="rounded-lg border border-zinc-200 bg-white p-3 shadow-sm">
      <ol className="grid gap-2 lg:grid-cols-4">
        {steps.map((step, index) => {
          const isActive = step.id === activeStep
          const isLocked = !step.isAvailable
          const StepIcon = getStepIcon(step)

          return (
            <li key={step.id}>
              <button
                aria-current={isActive ? 'step' : undefined}
                className={cn(
                  'flex h-full w-full items-center gap-3 rounded-lg border px-3 py-3 text-left transition',
                  isActive && 'border-emerald-600 bg-emerald-50 text-emerald-950 shadow-sm',
                  !isActive && step.isComplete && 'border-zinc-200 bg-white text-zinc-800 hover:border-emerald-300 hover:bg-emerald-50/50',
                  !isActive && !step.isComplete && !isLocked && 'border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50',
                  isLocked && 'cursor-not-allowed border-zinc-100 bg-zinc-50 text-zinc-400',
                )}
                disabled={isLocked}
                type="button"
                onClick={() => onStepChange(step.id)}
              >
                <span
                  className={cn(
                    'inline-flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold',
                    isActive && 'border-emerald-600 bg-emerald-600 text-white',
                    !isActive && step.isComplete && 'border-emerald-200 bg-emerald-100 text-emerald-700',
                    !isActive && !step.isComplete && !isLocked && 'border-zinc-200 bg-zinc-100 text-zinc-600',
                    isLocked && 'border-zinc-200 bg-white text-zinc-400',
                  )}
                >
                  {getStepIndicator({ index, isLocked, isComplete: step.isComplete, StepIcon })}
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">{t(`roundtable.stepper.steps.${step.id}.title`)}</span>
                  <span className="mt-0.5 block truncate text-xs opacity-75">{t(`roundtable.stepper.steps.${step.id}.description`)}</span>
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

function getStepIcon(step: RoundtableStep) {
  if (step.isComplete) return Check
  if (!step.isAvailable) return Lock
  return Circle
}

function getStepIndicator({
  index,
  isComplete,
  isLocked,
  StepIcon,
}: {
  index: number
  isComplete: boolean
  isLocked: boolean
  StepIcon: typeof Check
}) {
  if (isComplete) return <StepIcon className="size-4" />
  if (isLocked) return <StepIcon className="size-3.5" />
  return index + 1
}
