export type Citation = {
  source_id: string;
  source_url: string;
  citation_text: string;
};

type CitationListProps = {
  citations: Citation[];
};

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="chat-page__sources">
      <span>Sources</span>
      {citations.map((citation) => (
        <a href={citation.source_url} key={citation.source_id}>
          {citation.citation_text}
        </a>
      ))}
    </div>
  );
}
