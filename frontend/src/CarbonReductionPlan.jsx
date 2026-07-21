import React from 'react';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

export default function CarbonReductionPlan() {
  return (
    <div className="policy-page-wrapper">
      <AppHeader />
      
      <div className="policy-page">
        <div className="policy-page-header">
          <div className="policy-badge">PPN 06/21 · GHG Protocol</div>
          <h1>CarbonTally Ltd Carbon Reduction Plan</h1>
          <p className="policy-subtitle">
            Published under Procurement Policy Note 06/21. Sets out our FY 2024/25 baseline 
            greenhouse gas emissions, our interim reduction targets, and our committed pathway 
            to Net Zero by 2040.
          </p>
          
          <div className="policy-meta-grid">
            <div className="meta-item">
              <span className="meta-label">Publication Date</span>
              <span className="meta-value">{new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Baseline Year</span>
              <span className="meta-value">FY 2024/25</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Net Zero Target</span>
              <span className="meta-value">2040</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Standard</span>
              <span className="meta-value">PPN 06/21</span>
            </div>
          </div>
        </div>
        
        <div className="policy-content">
          {/* PPN Compliance Statement */}
          <section className="compliance-statement">
            <h2>PPN Compliance Statement</h2>
            <p>
              This Carbon Reduction Plan has been prepared and published in accordance with 
              <strong> Procurement Policy Note 06/21</strong> — the UK Government's requirement 
              for bidders on central-government contracts over £5 million to publish a Carbon 
              Reduction Plan committing to achieve Net Zero by 2050 or sooner. It follows the 
              PPN 06/21 Technical Standard, the GHG Protocol Corporate Accounting & Reporting 
              Standard, and the GHG Protocol Corporate Value Chain (Scope 3) Standard.
            </p>
          </section>

          {/* Section 1: Commitment */}
          <section>
            <h2>01 — Our commitment</h2>
            <h3>Net Zero by 2040</h3>
            <p>
              CarbonTally Ltd is committed to achieving Net Zero emissions by <strong>2040</strong>, 
              ten years ahead of the UK Government's 2050 commitment under the Climate Change Act 2008.
            </p>
            <p>
              As a carbon accounting software company, the credibility of our platform and advisory 
              services depends on demonstrable action within our own operations.
            </p>
            <p>
              This Carbon Reduction Plan sets out our baseline emissions, our interim reduction 
              targets, and the initiatives through which we will achieve Net Zero by 2040. Progress 
              will be reported annually in subsequent Carbon Reduction Plans and accompanying 
              SECR disclosures.
            </p>
          </section>

          {/* Section 2: Baseline Emissions */}
          <section>
            <h2>02 — Baseline emissions footprint</h2>
            <p>
              <strong>Baseline year:</strong> FY 2024/25 (1 June 2024 – 31 May 2025).
            </p>
            <p>
              Baseline emissions are the reference point against which emissions reduction is 
              measured. In accordance with the PPN 06/21 Technical Standard, and in the absence 
              of a prior assessed inventory, the FY 2024/25 reporting period has been used as 
              the baseline.
            </p>
            <p>
              The carbon footprint has been prepared in accordance with the GHG Protocol 
              Corporate Accounting and Reporting Standard, the Corporate Value Chain (Scope 3) 
              Standard, and the UK Government Environmental Reporting Guidelines (including SECR).
            </p>

            <h3>Organisational boundary & coverage</h3>
            <p>
              <strong>Boundary:</strong> operational control approach, covering one UK operational 
              facility during the reporting period.
            </p>
            <p>
              <strong>Scope coverage:</strong> all Scope 1 and Scope 2 emissions, together with 
              Scope 3 emissions in PPN 06/21 required categories (4, 5, 6, 7, 9) plus voluntary 
              disclosure of Scope 3 Category 1 (Purchased Goods & Services) and Category 3 
              (Fuel & Energy-Related Activities).
            </p>
            <p>
              <strong>Scope 2 reporting:</strong> both location-based (DEFRA 2025 UK grid factor) 
              and market-based (AIB UK residual mix) are reported in line with the GHG Protocol 
              Scope 2 Guidance.
            </p>

            <div className="table-wrapper">
              <table className="emissions-table">
                <thead>
                  <tr>
                    <th>Emissions</th>
                    <th>Total (tCO₂e)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>Scope 1</td><td>0.00</td></tr>
                  <tr><td>Scope 2 (location-based)</td><td>0.43</td></tr>
                  <tr><td>Scope 2 (market-based)</td><td>1.03</td></tr>
                  <tr><td>Scope 3 (included sources)</td><td>31.04</td></tr>
                  <tr className="total-row"><td><strong>Total emissions (location-based)</strong></td><td><strong>31.48</strong></td></tr>
                  <tr className="total-row"><td><strong>Total emissions (market-based)</strong></td><td><strong>32.07</strong></td></tr>
                </tbody>
              </table>
            </div>

            <h3>Scope 3 category coverage</h3>
            <div className="table-wrapper">
              <table className="emissions-table">
                <thead>
                  <tr>
                    <th>Cat</th>
                    <th>Description</th>
                    <th>PPN 06/21</th>
                    <th>Included</th>
                    <th>tCO₂e</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>1</td><td>Purchased Goods & Services</td><td>Not required</td><td>Yes (voluntary)</td><td>19.39</td></tr>
                  <tr><td>3</td><td>Fuel & Energy-Related Activities</td><td>Not required</td><td>Yes (voluntary)</td><td>0.17</td></tr>
                  <tr><td>4</td><td>Upstream Transportation & Distribution</td><td>Required</td><td>Yes</td><td>0.01</td></tr>
                  <tr><td>5</td><td>Waste Generated in Operations</td><td>Required</td><td>De minimis</td><td>0.00</td></tr>
                  <tr><td>6</td><td>Business Travel (air, rail, land, hotel)</td><td>Required</td><td>Yes</td><td>6.20</td></tr>
                  <tr><td>7</td><td>Employee Commuting (incl. WFH)</td><td>Required</td><td>Yes</td><td>5.28</td></tr>
                  <tr><td>9</td><td>Downstream Transportation & Distribution</td><td>Required</td><td>Not applicable</td><td>0.00</td></tr>
                  <tr className="total-row"><td colSpan="4"><strong>Total Scope 3</strong></td><td><strong>31.04</strong></td></tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 3: Current Emissions */}
          <section>
            <h2>03 — Current emissions reporting</h2>
            <p>
              <strong>Reporting year: FY 2024/25</strong>
            </p>
            <p>
              As FY 2024/25 is the baseline reporting period, the current reporting figures 
              match the baseline above. Year-on-year comparison will commence from FY 2025/26 
              onwards and will be published in subsequent Carbon Reduction Plans.
            </p>
          </section>

          {/* Section 4: Reduction Targets */}
          <section>
            <h2>04 — Emissions reduction targets</h2>
            <h3>Our trajectory to Net Zero</h3>
            <p>
              CarbonTally has adopted the following carbon reduction targets against the 
              FY 2024/25 market-based baseline of <strong>32.07 tCO₂e</strong>. Targets are 
              set on a market-based basis in line with the GHG Protocol Scope 2 Guidance.
            </p>

            <div className="targets-visual">
              <div className="target-bar">
                <div className="target-label">FY 2024/25</div>
                <div className="target-track">
                  <div className="target-fill" style={{ width: '100%' }}>32.07 t</div>
                </div>
              </div>
              <div className="target-bar">
                <div className="target-label">FY 2027/28 <span className="target-reduction">−25%</span></div>
                <div className="target-track">
                  <div className="target-fill" style={{ width: '75%' }}>24.05 t</div>
                </div>
              </div>
              <div className="target-bar">
                <div className="target-label">FY 2030/31 <span className="target-reduction">−50%</span></div>
                <div className="target-track">
                  <div className="target-fill" style={{ width: '50%' }}>16.04 t</div>
                </div>
              </div>
              <div className="target-bar">
                <div className="target-label">FY 2035/36 <span className="target-reduction">−75%</span></div>
                <div className="target-track">
                  <div className="target-fill" style={{ width: '25%' }}>8.02 t</div>
                </div>
              </div>
              <div className="target-bar">
                <div className="target-label">2040 <span className="target-reduction">Net Zero</span></div>
                <div className="target-track">
                  <div className="target-fill zero" style={{ width: '0%' }}>0.00 t</div>
                </div>
              </div>
            </div>

            <div className="table-wrapper">
              <table className="emissions-table">
                <thead>
                  <tr>
                    <th>Milestone</th>
                    <th>Reduction</th>
                    <th>Total emissions (tCO₂e)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>FY 2024/25 baseline</td><td>—</td><td>32.07</td></tr>
                  <tr><td>FY 2027/28</td><td>−25%</td><td>24.05</td></tr>
                  <tr><td>FY 2030/31</td><td>−50%</td><td>16.04</td></tr>
                  <tr><td>FY 2035/36</td><td>−75%</td><td>8.02</td></tr>
                  <tr className="total-row"><td><strong>2040 (Net Zero)</strong></td><td><strong>−100%</strong></td><td><strong>0.00</strong></td></tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 5: Reduction Projects */}
          <section>
            <h2>05 — Carbon reduction projects</h2>
            <h3>Initiatives completed and planned</h3>
            
            <h4>Completed initiatives (at or prior to baseline)</h4>
            <ul>
              <li>
                <strong>Remote-first operating model.</strong> CarbonTally operates as a 
                remote-first business, with only ad-hoc use of a shared managed-office facility. 
                This structurally eliminates the majority of commuter transport emissions and 
                materially reduces office energy consumption.
              </li>
              <li>
                <strong>Travel-avoidance culture.</strong> Non-essential business travel is 
                actively avoided in favour of virtual meetings. Where travel is required, 
                lower-carbon options are prioritised.
              </li>
              <li>
                <strong>Rail-over-road preference.</strong> Where journey time allows, rail 
                is selected in preference to driving for domestic business travel.
              </li>
              <li>
                <strong>Cloud-native infrastructure.</strong> Our SaaS platform runs on 
                efficient cloud infrastructure, minimising on-premise energy consumption.
              </li>
            </ul>

            <h4>Future initiatives</h4>
            <ul>
              <li>
                <strong>Supplier engagement programme.</strong> Direct engagement with top 
                supplier hotspots to request their own Carbon Reduction Plans. Progressive 
                reweighting of spend toward suppliers with credible reduction commitments.
              </li>
              <li>
                <strong>Formalised sustainable travel policy.</strong> Virtual-first for 
                internal and prospect meetings; rail-first for journeys under six hours; 
                economy-class direct flights only.
              </li>
              <li>
                <strong>Renewable electricity procurement.</strong> Securing a REGO-backed 
                renewable electricity supply at any office facility.
              </li>
              <li>
                <strong>Employee home-working guidance.</strong> Publishing guidance for 
                employees on energy-efficient home working.
              </li>
              <li>
                <strong>Improved data quality.</strong> Transitioning from spend-based to 
                activity- or supplier-specific emission factors.
              </li>
            </ul>
          </section>

          {/* Section 6: Declaration */}
          <section>
            <h2>06 — Declaration & sign off</h2>
            <h3>Board declaration</h3>
            <p>
              This Carbon Reduction Plan has been completed in accordance with PPN 06/21 
              and associated guidance and reporting standard for Carbon Reduction Plans.
            </p>
            <p>
              Emissions have been reported and recorded in accordance with the published 
              reporting standard for Carbon Reduction Plans and the GHG Reporting Protocol 
              Corporate Standard, and use the appropriate UK Government conversion factors 
              for greenhouse gas company reporting.
            </p>
            <p>
              Scope 1 and Scope 2 emissions have been reported in accordance with SECR 
              requirements, and the required subset of Scope 3 emissions has been reported 
              in accordance with the published reporting standard for Carbon Reduction Plans 
              and the Corporate Value Chain (Scope 3) Standard.
            </p>
            <p>
              This Carbon Reduction Plan has been reviewed and signed off by the board of directors.
            </p>

            <div className="signoff-box">
              <p><strong>Signed on behalf of the supplier</strong></p>
              <p>[Shomon Robie]</p>
              <p><strong>Job title:</strong> Chief Executive Officer</p>
              <p><strong>Organisation:</strong> CarbonTally UK Ltd</p>
              <p><strong>Date:</strong> {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
            </div>
          </section>
        </div>
      </div>
      
      <AppFooter />
    </div>
  );
}