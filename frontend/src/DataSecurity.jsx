import React from 'react';
import { Link } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

export default function DataSecurity() {
  const assessmentAreas = [
    'Authentication', 'Authorization', 'RBAC', 'Organization isolation',
    'Supabase RLS', 'Storage security', 'Realtime access', 'API security',
    'Background processing', 'File processing', 'Secrets management',
    'Dependencies', 'Deployment configuration', 'Logging', 'Data lifecycle'
  ];

  const roles = [
    ['Customer users', 'Access their organization’s authorized data and processing results.'],
    ['Consultants', 'Manage authorized client organizations according to their permissions.'],
    ['Data Extractors', 'Process assigned extraction jobs.'],
    ['Data Validators', 'Review and validate assigned processing results.'],
    ['QA / Supervisors', 'Review or manage processing activities within their authorized scope.'],
    ['Administrators', 'Perform additional platform-management functions according to their permissions.']
  ];

  return (
    <div className="policy-page-wrapper">
      <AppHeader />

      <div className="policy-page">
        <div className="policy-page-header">
          <div className="about-hero">
            <div className="about-logo-container">
              <span className="logo-icon" style={{ fontSize: '3rem' }}>🔐</span>
              <span className="logo-text" style={{ fontSize: '2.5rem', fontWeight: 700 }}>
                CarbonTally
              </span>
            </div>
            <h1>Data Security at CarbonTally</h1>
            <p className="policy-subtitle">
              Secure, controlled and accountable data processing for the documents
              and datasets you entrust to us.
            </p>
          </div>
        </div>

        <div className="policy-content">
          <section>
            <h2>Secure, controlled and accountable data processing</h2>
            <p>
              CarbonTally processes business documents and datasets that may contain
              commercially sensitive information and, in some cases, personal information.
            </p>
            <p>Our platform is designed around a simple principle:</p>
            <blockquote>
              <strong>People should only have access to the data they need, for the work they are authorized to perform.</strong>
            </blockquote>
            <p>
              Whether data is processed automatically by CarbonTally or requires human
              extraction and validation, we use controlled workflows designed to protect
              customer information throughout the processing lifecycle.
            </p>
          </section>

          <section>
            <h2>Security by design</h2>
            <p>
              CarbonTally is built as a multi-tenant data-processing platform. Customer
              organizations are logically separated, with access controls designed to
              ensure that users can access only the organizations, documents and
              processing activities they are authorized to access.
            </p>
            <ul>
              <li>Organization-level data isolation</li>
              <li>Role-based access control</li>
              <li>Private document storage</li>
              <li>Controlled document access</li>
              <li>Assigned processing jobs</li>
              <li>Least-privilege access</li>
              <li>Human-processing controls</li>
              <li>Activity and audit tracking</li>
              <li>Secure authentication</li>
              <li>Controlled API access</li>
              <li>Data lifecycle controls</li>
            </ul>
            <p>Security is applied at multiple layers rather than relying solely on the user interface.</p>
          </section>

          <section>
            <h2>Your documents remain under controlled access</h2>
            <p>Customers may upload documents including:</p>
            <ul>
              <li>PDF</li><li>CSV</li><li>Excel / XLSX</li><li>Images</li>
              <li>Other supported business documents</li>
            </ul>
            <p>
              Documents are stored within controlled application infrastructure and are
              not intended to be exposed through public file links.
            </p>
            <p>
              Access to a document is governed by the user’s authorization and the
              processing workflow associated with that document.
            </p>
          </section>

          <section>
            <h2>Human-in-the-loop processing</h2>
            <p>
              Automation is an important part of CarbonTally, but we recognize that not
              every business document can be reliably processed without human review.
            </p>
            <div className="security-flow">
              {['Customer Document', 'Automated Processing', 'Human Review Required?', 'Assigned Processing Job',
                'Authorized Operator', 'Controlled Document Viewer', 'Data Extraction',
                'Validation / QA', 'Structured Carbon Data'].map((item, i, arr) => (
                <React.Fragment key={item}>
                  <div>{item}</div>
                  {i < arr.length - 1 && <span>↓</span>}
                </React.Fragment>
              ))}
            </div>
            <p>
              Human processing is performed through CarbonTally’s controlled processing
              workspace rather than requiring operators to routinely download customer
              documents and process them locally.
            </p>
          </section>

          <section>
            <h2>Least-privilege processing</h2>
            <p>Our processing model is based on <strong>need-to-know access</strong>.</p>
            <p>
              A data-processing operator does not need unrestricted access to CarbonTally’s
              customer database. The intended workflow is:
            </p>
            <blockquote>
              <strong>Assigned job → required document → required fields → required action</strong>
            </blockquote>
            <p>
              An operator assigned to extract information from a particular document
              should not automatically receive access to unrelated customer organizations,
              documents, queues or account information.
            </p>
          </section>

          <section>
            <h2>Controlled access for processing personnel</h2>
            <p>
              CarbonTally’s manual data-processing services may be provided by authorized
              personnel working through our processing operation.
            </p>
            <ul>
              <li>Data Extractors</li><li>Data Validators</li><li>QA personnel</li>
              <li>Supervisors</li><li>Other authorized processing personnel</li>
            </ul>
            <p>
              Access is intended to be role-based and limited according to the responsibilities
              of each role. Each individual should use their own authorized account rather
              than shared credentials.
            </p>
          </section>

          <section>
            <h2>Secure document viewing</h2>
            <p>
              For restricted processing roles, the normal workflow is designed around
              <strong> viewing and processing documents within CarbonTally</strong>, rather
              than downloading source documents to personal devices.
            </p>
            <div className="security-feature-grid">
              {[
                ['👁️', 'Controlled viewing', 'Operators work with source documents inside the processing workspace.'],
                ['🧩', 'Assigned jobs', 'Access is tied to the work the operator is authorized to perform.'],
                ['📝', 'Structured extraction', 'Data is entered directly into CarbonTally rather than processed through local files.'],
                ['🔎', 'Traceable actions', 'Important processing actions can be associated with authenticated users and jobs.']
              ].map(([icon, title, text]) => (
                <div className="security-feature-card" key={title}>
                  <span className="feature-icon">{icon}</span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              ))}
            </div>
            <p>
              Where appropriate, CarbonTally may also use document watermarks and other
              controls to improve traceability. These controls are intended to reduce
              unnecessary copying and improve accountability; they cannot guarantee
              prevention of screenshots, screen recording or other forms of physical copying.
            </p>
          </section>

          <section>
            <h2>Data minimisation</h2>
            <p>
              We aim to show processing personnel only the information necessary to perform
              their assigned task. An operator extracting information from an invoice may
              need to see the invoice and relevant extraction fields, but does not
              necessarily need access to the customer’s complete account, unrelated
              documents, historical records or customer administration.
            </p>
          </section>

          <section>
            <h2>Role-based access</h2>
            <p>CarbonTally uses role-based access principles across its workspaces.</p>
            <div className="security-role-grid">
              {roles.map(([title, text]) => (
                <div key={title}><h3>{title}</h3><p>{text}</p></div>
              ))}
            </div>
            <p>
              Actual permissions are enforced through application and data-access controls
              rather than relying only on what a user can see in the interface.
            </p>
          </section>

          <section>
            <h2>Organization-level data isolation</h2>
            <p>
              CarbonTally is designed as a multi-tenant platform. Customer data belongs
              to an organization and access is controlled around that organizational boundary.
            </p>
            <p>
              Our security model is designed to prevent a user belonging to one organization
              from accessing another organization’s documents, extracted data, processing
              jobs, validation records, emissions data, exports, messages or other
              organization-specific information.
            </p>
            <p>Database-level access controls form an important part of this model.</p>
          </section>

          <section>
            <h2>Secure application infrastructure</h2>
            <p>
              CarbonTally uses established managed technology providers as part of its
              application infrastructure, including:
            </p>
            <ul><li>Supabase</li><li>Vercel</li><li>Render</li><li>Resend</li></ul>
            <p>
              These providers operate infrastructure-level security controls within their
              respective services. CarbonTally remains responsible for the security of its
              own application code, configuration, authorization model, database policies,
              storage configuration and use of these services.
            </p>
          </section>

          <section>
            <h2>Authentication and authorization</h2>
            <p>
              Access to CarbonTally is authenticated and authorized according to the user’s
              account and permissions.
            </p>
            <ul>
              <li>Authenticated users</li><li>Organization membership</li>
              <li>Role-based permissions</li><li>Resource-level authorization</li>
              <li>Organization-level isolation</li><li>Controlled processing assignments</li>
            </ul>
            <p>
              Frontend visibility alone is not intended to be the security boundary.
              Authorization should also be enforced at the appropriate backend and
              data-access layers.
            </p>
          </section>

          <section>
            <h2>API security</h2>
            <p>
              CarbonTally is designed to support both web-based processing and machine-to-machine
              data processing. API access is therefore treated as a security boundary.
              API requests should be authenticated and authorized according to the organization,
              user or API credential making the request.
            </p>
            <p>Resource identifiers should not themselves grant access to customer information.</p>
          </section>

          <section>
            <h2>Secure processing infrastructure</h2>
            <div className="security-flow">
              {['Upload', 'Storage', 'Processing Job', 'Extraction', 'Normalization',
                'Emission Factor Mapping', 'Validation', 'Customer Review', 'Structured Data']
                .map((item, i, arr) => (
                  <React.Fragment key={item}>
                    <div>{item}</div>
                    {i < arr.length - 1 && <span>↓</span>}
                  </React.Fragment>
                ))}
            </div>
            <p>
              Security and organization context should remain associated with the data
              throughout this workflow, including automated and background processing.
            </p>
          </section>

          <section>
            <h2>Bangladesh processing operations</h2>
            <p>
              CarbonTally’s manual data-processing services may be provided by
              <strong> Babui Limited in Bangladesh</strong>, under a formal business and
              data-processing arrangement with CarbonTally UK Limited.
            </p>
            <p>
              Babui Limited maintains an ISO 27001 certification for its relevant operations.
              The precise scope of that certification applies according to the certification
              documentation and is not represented as certification of CarbonTally UK Limited
              or the CarbonTally platform.
            </p>
            <p>
              Authorized processing personnel may work remotely, subject to appropriate
              contractual, confidentiality, security and access-control requirements.
            </p>
            <div className="security-flow">
              {['CarbonTally UK', 'Controlled processing arrangement', 'Babui Limited',
                'Authorized processing personnel', 'Assigned CarbonTally jobs'].map((item, i, arr) => (
                <React.Fragment key={item}>
                  <div>{item}</div>
                  {i < arr.length - 1 && <span>↓</span>}
                </React.Fragment>
              ))}
            </div>
          </section>

          <section>
            <h2>International data processing</h2>
            <p>
              Where customer personal information is made accessible to a separate organization
              outside the UK, applicable international-transfer requirements need to be considered.
            </p>
            <p>
              CarbonTally’s contractual and technical arrangements are designed to support
              controlled processing and appropriate security measures. Customer-specific
              contractual arrangements may include appropriate data-processing and international
              transfer provisions.
            </p>
            <p>
              For UK and EU customers, applicable privacy and international transfer requirements
              are assessed according to the relevant relationship and processing activities.
            </p>
          </section>

          <section>
            <h2>Data processing agreements</h2>
            <p>
              Where CarbonTally acts as a processor on behalf of a customer, appropriate
              contractual arrangements are used to govern the processing of personal information.
            </p>
            <ul>
              <li>Processing instructions</li><li>Categories of data</li><li>Processing purposes</li>
              <li>Confidentiality</li><li>Security measures</li><li>Sub-processors</li>
              <li>International transfers</li><li>Data-subject rights</li>
              <li>Security incidents</li><li>Data deletion or return</li>
              <li>Audit and compliance assistance</li>
            </ul>
          </section>

          <section>
            <h2>Security assessment</h2>
            <p>
              CarbonTally is undertaking an internal application security assessment covering
              areas including:
            </p>
            <div className="security-tag-list">
              {assessmentAreas.map(item => <span className="security-tag" key={item}>{item}</span>)}
            </div>
            <p>
              The purpose of this assessment is to identify weaknesses in CarbonTally’s
              application and recommend remediation.
            </p>
            <div className="security-notice">
              <strong>Important:</strong> An internal assessment should not be interpreted as
              an independent third-party penetration test. Where an independent security
              assessment or penetration test is completed, CarbonTally may publish appropriate
              information about that assessment separately.
            </div>
          </section>

          <section>
            <h2>Security is an ongoing process</h2>
            <p>
              Security is not a one-time certification or a single technical control.
              As CarbonTally grows, we expect our security practices to evolve.
            </p>
            <ul>
              <li>Reviewing application access controls</li>
              <li>Testing organization isolation</li>
              <li>Reviewing database security policies</li>
              <li>Monitoring dependencies</li>
              <li>Protecting application secrets</li>
              <li>Improving auditability</li>
              <li>Reviewing document-processing workflows</li>
              <li>Managing personnel access</li>
              <li>Reviewing third-party services</li>
              <li>Periodically reassessing security risks</li>
            </ul>
          </section>

          <section>
            <h2>What we do not claim</h2>
            <p>
              CarbonTally does not use this page to claim certifications or independent
              assessments that have not actually been completed.
            </p>
            <ul>
              <li>PCI DSS certification</li>
              <li>SOC 2 certification</li>
              <li>ISO 27001 certification of CarbonTally UK Limited</li>
              <li>Independent penetration-test certification</li>
              <li>Independent carbon-accounting assurance</li>
              <li>Guaranteed prevention of screenshots or copying</li>
              <li>That every customer deployment has identical security requirements</li>
            </ul>
            <p>
              Where formal certifications or independent assessments apply to a particular
              group company or service provider, we describe them according to their actual scope.
            </p>
          </section>

          <section>
            <h2>Responsible security</h2>
            <p>
              If you believe you have identified a security issue affecting CarbonTally,
              please contact our security team through the designated security contact.
            </p>
            <p>
              Please do not attempt to access, modify, download or disclose another
              customer’s information.
            </p>
            <p>
              We appreciate responsible reporting that allows us to investigate and address
              security issues.
            </p>
          </section>

          <section className="cta-section">
            <h2>Security is part of responsible data processing</h2>
            <p>
              CarbonTally combines controlled access, least privilege, human accountability
              and secure processing to help businesses turn difficult source data into
              structured carbon data.
            </p>
            <div className="cta-buttons">
              <Link to="/contact" className="btn-primary btn-gradient">
                Contact CarbonTally
              </Link>
              <Link to="/privacy-policy" className="btn-outline">
                View Privacy Policy
              </Link>
            </div>
          </section>
        </div>
      </div>

      <AppFooter />
    </div>
  );
}
