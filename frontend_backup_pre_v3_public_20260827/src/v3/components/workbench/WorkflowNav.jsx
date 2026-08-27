// frontend/src/v3/components/workbench/WorkflowNav.jsx
// D19 — TOP workflow navigation for the processing workbench. Steps are
// rendered as a horizontal stepper (Queue → Extract → Map → Validate → Review
// → QC → Evidence by default) with complete/current/upcoming states.
import React from 'react';
import Icon from '../ui/Icon';

export const DEFAULT_STAGES = [
  { id: 'queue', label: 'Queue' },
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'validate', label: 'Validate' },
  { id: 'review', label: 'Review' },
  { id: 'qc', label: 'QC' },
  { id: 'evidence', label: 'Evidence' },
];

export default function WorkflowNav({ stages = DEFAULT_STAGES, current, onStep, disabled }) {
  const currentIndex = stages.findIndex((s) => s.id === current);

  return (
    <nav className="ct-wb-steps" aria-label="Processing workflow">
      {stages.map((stage, i) => {
        const isComplete = currentIndex > i;
        const isCurrent = currentIndex === i;
        const canNavigate = typeof onStep === 'function' && !disabled;
        return (
          <React.Fragment key={stage.id}>
            {i > 0 && <span className="ct-wb-sep" aria-hidden="true">›</span>}
            <button
              type="button"
              className={`ct-wb-step${isComplete ? ' ct-wb-step--complete' : ''}`}
              aria-current={isCurrent ? 'step' : undefined}
              disabled={!canNavigate}
              onClick={canNavigate ? () => onStep(stage.id) : undefined}
              title={stage.title}
            >
              <span className="ct-wb-step__num" aria-hidden="true">
                {isComplete ? <Icon name="check" size={12} /> : i + 1}
              </span>
              {stage.label}
            </button>
          </React.Fragment>
        );
      })}
    </nav>
  );
}
