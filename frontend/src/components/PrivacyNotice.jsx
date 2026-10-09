import React from 'react'
import { Modal } from './ui.jsx'

const CONTACT = import.meta.env.VITE_PRIVACY_CONTACT || 'the team running this SolarSabha instance'

// Plain-language notice, written for a society secretary. Version is recorded with each consent.
export default function PrivacyNotice({ onClose }) {
  return (
    <Modal title="Privacy notice (version 2026-10)" onClose={onClose} wide>
      <div className="prose">
        <h4>What SolarSabha stores</h4>
        <p>Your society's details, the electricity bills and vendor quotations you upload (the files and the numbers read from them),
          the names and roles of committee members you add, the letters it drafts, and a log of who changed what.</p>
        <h4>Why</h4>
        <p>Only to size the solar system, check quotations, prepare meeting papers and letters, and track the DISCOM process for your committee.
          Nothing is sold, shared for advertising, or sent to anyone on your behalf. The app cannot send email, sign, pay or file anything.</p>
        <h4>Where it is kept</h4>
        <p>When deployed on AWS, data is stored in the Mumbai region (ap-south-1), encrypted at rest. When AI reading is switched on, documents
          are read by Amazon Bedrock using an India-only inference profile; Bedrock does not use your documents to train models.
          In the offline mode, documents are read on the server with plain rules and no AI.</p>
        <h4>Who can see it</h4>
        <p>Anyone who has your project's link, because the link contains its access key. Share it only with your committee. Member names are
          chosen by the person using the link; for verified sign-in, the operator can enable an identity provider.</p>
        <h4>How long</h4>
        <p>A project is deleted automatically one year after it is created. The secretary can export everything or delete the project at any
          time from Settings. Deleting removes the uploaded files and all stored data.</p>
        <h4>Your rights</h4>
        <p>Under India's Digital Personal Data Protection Act, 2023, you can ask to see, correct or erase your personal data, and raise a
          grievance. Use Settings to export, correct or delete, or contact {CONTACT}.</p>
        <p className="fine">This browser remembers the projects you open (in local storage) so you can come back to them. No tracking cookies are used.</p>
      </div>
    </Modal>
  )
}
