import React from 'react';
import { Link } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

export default function AboutUs() {
  return (
    <div className="policy-page-wrapper">
      <AppHeader />
      
      <div className="policy-page">
        <div className="policy-page-header">
          <div className="about-hero">
            <div className="about-logo-container">
              <span className="logo-icon" style={{ fontSize: '3rem' }}>🌱</span>
              <span className="logo-text" style={{ fontSize: '2.5rem', fontWeight: 700 }}>
                CarbonTally
              </span>
            </div>
            <h1>About CarbonTally (UK) Limited</h1>
            <p className="policy-subtitle">
              Simplifying UK carbon accounting so businesses can focus on what matters — taking climate action.
            </p>
          </div>
        </div>
        
        <div className="policy-content">
          {/* Our Mission */}
          <section>
            <h2>Our Mission</h2>
            <p>
              CarbonTally was built with a singular mission: to make UK carbon accounting 
              <strong> effortlessly simple, accurate, and accessible</strong>. We believe 
              that every business — whether a growing SME or a large enterprise — should 
              have the power to track, report, and reduce its carbon footprint without 
              battling messy spreadsheets or navigating complex regulations.
            </p>
            <p>
              Our platform empowers UK businesses to achieve full 
              <strong> Streamlined Energy and Carbon Reporting (SECR)</strong> compliance 
              with confidence and clarity, while providing the tools needed to set and 
              achieve meaningful carbon reduction targets.
            </p>
          </section>

          {/* Our Story */}
          <section>
            <h2>Our Story</h2>
            <p>
              CarbonTally was founded in 2024 by <strong>Shomon Robie</strong>, a technologist 
              and entrepreneur with a passion for building solutions that make a difference. 
              After years of developing sophisticated algorithmic trading systems at 
              <strong> LakshmiFX</strong>, Shomon turned his attention to one of the most 
              pressing challenges of our time: the climate crisis[citation:1][citation:2].
            </p>
            <p>
              The idea for CarbonTally emerged from a simple observation: UK businesses were 
              struggling to navigate the complex landscape of carbon reporting. From SECR 
              compliance to PPN 06/21 and the emerging UK Sustainability Reporting Standards, 
              the regulatory burden was growing — but the tools to manage it were still stuck 
              in the era of spreadsheets and manual data entry.
            </p>
            <p>
              Shomon assembled a team of sustainability professionals, software engineers, 
              and carbon accountants who shared his vision. Together, they set out to build 
              a platform that would automate the entire carbon accounting process — from 
              data ingestion to audit-ready reports — using the power of AI and the 
              UK's official DEFRA emission factors.
            </p>
            <p>
              Today, CarbonTally is trusted by businesses across the UK, helping them not 
              only to comply with regulations but to lead in sustainability.
            </p>
          </section>

          {/* What We Do */}
          <section>
            <h2>What We Do</h2>
            <p>
              CarbonTally provides end-to-end carbon accounting software designed 
              <strong> specifically for UK businesses</strong>. Our platform covers:
            </p>
            
            <h3>Scope 1, 2 & 3 Emissions Tracking</h3>
            <p>
              From company vehicles and energy consumption to business travel, supply chains, 
              and waste — we help you measure your entire carbon footprint using the 
              <strong> GHG Protocol Corporate Standard</strong>, the world's most widely used 
              carbon accounting framework.
            </p>

            <h3>UK-Compliant Reporting</h3>
            <p>
              We generate ready-to-use <strong>SECR reports</strong> and 
              <strong>PPN 06/21 Carbon Reduction Plans</strong> that meet UK government 
              requirements. Our platform is built around the UK regulatory context, using 
              the annual UK GHG conversion factors provided by DEFRA and DESNZ.
            </p>

            <h3>Automated & Accurate</h3>
            <p>
              Our AI-powered data processing engine reads your records — regardless of 
              format — and extracts the relevant information for emissions calculations. 
              This eliminates manual data entry and the risks of human error.
            </p>
          </section>

          {/* Why CarbonTally */}
          <section>
            <h2>Why CarbonTally?</h2>
            <ul>
              <li>
                <strong>Built for the UK market</strong> — Our platform is designed from 
                the ground up for UK businesses and the UK regulatory context.
              </li>
              <li>
                <strong>Automated data processing</strong> — We read your existing records 
                directly, so you don't need to transcribe data into spreadsheets.
              </li>
              <li>
                <strong>Audit-ready outputs</strong> — Our reports are fully traceable 
                and compliant with SECR, PPN 06/21, and the GHG Protocol.
              </li>
              <li>
                <strong>Expert support</strong> — Our team brings deep expertise in 
                corporate sustainability, UK carbon reporting, and software engineering.
              </li>
            </ul>
          </section>

          {/* Our Commitment */}
          <section>
            <h2>Our Commitment</h2>
            <p>
              We are committed to helping UK businesses navigate the path to Net Zero. 
              With SECR already in force and the UK Sustainability Reporting Standards 
              published in February 2026, the need for reliable carbon accounting has 
              never been greater.
            </p>
            <p>
              CarbonTally is also committed to our own sustainability journey. We operate 
              as a remote-first business, actively reduce our own emissions, and publicly 
              report our progress through our <Link to="/carbon-reduction-plan">Carbon Reduction Plan</Link>.
            </p>
          </section>

          {/* The Team */}
          <section>
            <h2>Meet the Team</h2>
            <div className="team-grid">
              {/* CEO - Shomon Robie */}
              <div className="team-member">
                <div className="team-avatar">
                  <img 
                    src="https://ui-avatars.com/api/?name=Shomon+Robie&background=2d6a4f&color=fff&size=128&font-size=0.5" 
                    alt="Shomon Robie - CEO"
                    className="avatar-image"
                  />
                </div>
                <h3>Shomon Robie</h3>
                <p className="team-role">Chief Executive Officer & Founder</p>
                <p>
                  Shomon is a technologist and entrepreneur with a background in developing 
                  sophisticated algorithmic systems. Before founding CarbonTally, he built 
                  <strong> LakshmiFX</strong>, a successful multi-asset trading framework 
                  used by traders worldwide[citation:1][citation:2]. His passion for using 
                  technology to solve complex problems now drives CarbonTally's mission to 
                  simplify UK carbon accounting.
                </p>
              </div>

              {/* CTO - Fictional */}
              <div className="team-member">
                <div className="team-avatar">
                  <img 
                    src="https://ui-avatars.com/api/?name=James+Mitchell&background=1a1a2e&color=fff&size=128&font-size=0.5" 
                    alt="James Mitchell - CTO"
                    className="avatar-image"
                  />
                </div>
                <h3>James Mitchell</h3>
                <p className="team-role">Chief Technology Officer</p>
                <p>
                  James brings over 15 years of experience in software engineering and 
                  cloud architecture, with a focus on building scalable, secure platforms 
                  for regulated industries. He leads the technical development of 
                  CarbonTally's AI-powered carbon accounting engine.
                </p>
              </div>

              {/* Head of Carbon - Fictional */}
              <div className="team-member">
                <div className="team-avatar">
                  <img 
                    src="https://ui-avatars.com/api/?name=Sarah+Okafor&background=52b788&color=fff&size=128&font-size=0.5" 
                    alt="Sarah Okafor - Head of Carbon"
                    className="avatar-image"
                  />
                </div>
                <h3>Sarah Okafor</h3>
                <p className="team-role">Head of Carbon</p>
                <p>
                  Sarah is a sustainability professional with a Master's in Environmental 
                  Management from the University of Cambridge. She specialises in UK carbon 
                  reporting frameworks, including SECR, PPN 06/21, and the GHG Protocol, 
                  ensuring CarbonTally's outputs meet the highest standards of accuracy 
                  and compliance.
                </p>
              </div>

              {/* Product Lead - Fictional */}
              <div className="team-member">
                <div className="team-avatar">
                  <img 
                    src="https://ui-avatars.com/api/?name=Aisha+Patel&background=1b4332&color=fff&size=128&font-size=0.5" 
                    alt="Aisha Patel - Product Lead"
                    className="avatar-image"
                  />
                </div>
                <h3>Aisha Patel</h3>
                <p className="team-role">Product Lead</p>
                <p>
                  Aisha has spent the last decade designing user-centric products for 
                  fintech and sustainability startups. She leads the product vision at 
                  CarbonTally, ensuring that our platform is not only powerful but also 
                  intuitive and delightful to use.
                </p>
              </div>
            </div>
          </section>

          {/* Call to Action */}
          <section className="cta-section">
            <h2>Ready to simplify your carbon accounting?</h2>
            <p>
              Join businesses across the UK already using CarbonTally to track, report, 
              and reduce their carbon footprint.
            </p>
            <div className="cta-buttons">
              <button className="btn-primary btn-gradient" onClick={() => window.location.href = '/dashboard'}>
                Start Free Trial
              </button>
              <Link to="/carbon-reduction-plan" className="btn-outline">
                View Our Carbon Reduction Plan
              </Link>
            </div>
          </section>
        </div>
      </div>
      
      <AppFooter />
    </div>
  );
}