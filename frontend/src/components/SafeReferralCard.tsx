type SafeReferralCardProps = {
  officeName: string;
  reason: string;
  contactUrl?: string;
};

export function SafeReferralCard({
  officeName,
  reason,
  contactUrl,
}: SafeReferralCardProps) {
  return (
    <aside className="chat-page__referral-card" role="note">
      <strong>Verified next step</strong>
      <span>{officeName}</span>
      <p>{reason}</p>
      {contactUrl && <a href={contactUrl}>Open official contact</a>}
    </aside>
  );
}
