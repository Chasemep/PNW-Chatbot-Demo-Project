import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ContactReferral } from "../src/components/ContactReferral";

describe("contact referral UI", () => {
  it("renders verified contact details with an official link", () => {
    const markup = renderToStaticMarkup(
      createElement(ContactReferral, {
        officeName: "Registrar",
        reason: "Contact the Registrar for registration assistance.",
        contactUrl: "https://www.pnw.edu/registrar/",
        contactEmail: "registrar@pnw.edu",
        contactPhone: "219-555-0123",
      }),
    );

    expect(markup).toContain("Registrar");
    expect(markup).toContain("registration assistance");
    expect(markup).toContain('href="https://www.pnw.edu/registrar/"');
    expect(markup).toContain('href="mailto:registrar@pnw.edu"');
    expect(markup).toContain('href="tel:2195550123"');
    expect(markup).toContain("Open official contact");
  });

  it("renders the official directory link when a specific contact is unavailable", () => {
    const markup = renderToStaticMarkup(
      createElement(ContactReferral, {
        officeName: "Purdue Northwest directory",
        reason: "Use the official directory to locate the right office.",
        contactUrl: "https://www.pnw.edu/academic-and-administrative-offices/",
      }),
    );

    expect(markup).toContain(
      'href="https://www.pnw.edu/academic-and-administrative-offices/"',
    );
    expect(markup).toContain("Open official directory");
  });
});