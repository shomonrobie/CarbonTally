// frontend/src/CarbonReductionPlan.jsx
// Carbon Reduction Plan (PPN 06/21). Rewritten as a pre-launch DRAFT:
// specific emissions figures, a fixed publication date and a signed-off
// declaration cannot be truthfully published until the company has verified
// baseline data. The Product Owner must supply verified data before launch.
import React from 'react';
import PageShell from './public/PageShell';

export default function CarbonReductionPlan() {
  return (
    <PageShell
      title="Carbon Reduction Plan — CarbonTally"
      description="CarbonTally's Carbon Reduction Plan under Procurement Policy Note 06/21. Draft for review ahead of commercial launch."
    >
      <div className="ct-page">
        <h1>Carbon Reduction Plan</h1>
        <p className="ct-page-meta">CarbonTally Ltd · Procurement Policy Note 06/21</p>

        <div className="ct-legal-note">
          This plan is a pre-launch draft. Emissions baselines, reduction targets and the
          formal declaration will be completed with verified company data before
          publication at commercial launch.
        </div>

        <h2>1. Commitment</h2>
        <p>
          CarbonTally Ltd is committed to achieving Net Zero. As a carbon-accounting
          platform, the credibility of our product depends on credible action within our
          own operations. A Net Zero target year and interim reduction milestones will be
          set out when the verified baseline is published.
        </p>

        <h2>2. Baseline emissions</h2>
        <p>
          The baseline reporting period and baseline emissions figure will be published
          here once the company&apos;s first verified greenhouse-gas inventory has been
          completed. The inventory will be prepared in accordance with the GHG Protocol
          Corporate Accounting and Reporting Standard and UK Government conversion
          factors for company reporting.
        </p>

        <h2>3. Reduction targets</h2>
        <p>
          Interim reduction targets and the trajectory to Net Zero will be published with
          the baseline. Progress will be reported annually.
        </p>

        <h2>4. Reduction initiatives</h2>
        <p>
          CarbonTally operates a remote-first model, which structurally limits commuting
          and office-energy emissions, and prefers virtual meetings and rail travel for
          domestic business journeys. Further initiatives — including supplier
          engagement and renewable electricity procurement — will be documented in the
          published plan.
        </p>

        <h2>5. Declaration</h2>
        <p>
          This draft has not yet been formally declared. The completed plan will be
          reviewed and signed off by the board of CarbonTally Ltd before publication.
        </p>
      </div>
    </PageShell>
  );
}
