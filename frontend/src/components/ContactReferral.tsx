type ContactReferralProps = {
  officeName: string;
  reason: string;
  contactUrl?: string;
  contactEmail?: string;
  contactPhone?: string;
};

export function ContactReferral({
  officeName,
  reason,
  contactUrl,
  contactEmail,
  contactPhone,
}: ContactReferralProps) {
  const phoneLink = contactPhone?.replace(/[^\d+]/g, "");
  const isDirectoryFallback = officeName.toLowerCase().includes("directory");

  return (
    <aside className="chat-page__referral-card" role="note">
      <strong>Verified next step</strong>
      <span>{officeName}</span>
      <p>{reason}</p>
      {contactEmail && <a href={`mailto:${contactEmail}`}>{contactEmail}</a>}
      {contactPhone && <a href={`tel:${phoneLink}`}>{contactPhone}</a>}
      {contactUrl && (
        <a href={contactUrl}>
          {isDirectoryFallback ? "Open official directory" : "Open official contact"}
        </a>
      )}
    </aside>
  );
}