import type { FileReference } from "./api-client";

export const citationStyles = ["IEEE", "APA 7", "Harvard", "MLA 9"] as const;

export type CitationStyle = (typeof citationStyles)[number];

export function citationMarker(reference: FileReference, style: CitationStyle): string {
  if (style === "IEEE") return `[${reference.number}]`;
  const { surname, year } = citationParts(reference);
  if (style === "APA 7") return `(${surname}, ${year})`;
  if (style === "Harvard") return `(${surname} ${year})`;
  return `(${surname})`;
}

export function formatReference(reference: FileReference, style: CitationStyle): string {
  if (style === "IEEE") {
    return reference.citation.replace(/^\[\d+\]/, `[${reference.number}]`);
  }
  const { authors, title, source, year, doi } = citationParts(reference);
  const authorText = authors || reference.filename;
  const doiText = doi ? ` https://doi.org/${doi}` : "";
  if (style === "APA 7") {
    return `${authorText} (${year}). ${title}. ${source}.${doiText}`.replace(/\s+\./g, ".").trim();
  }
  if (style === "Harvard") {
    return `${authorText} (${year}) '${title}', ${source}.${doiText}`.replace(/\s+\./g, ".").trim();
  }
  return `${authorText}. “${title}.” ${source}, ${year}.${doiText}`.replace(/\s+\./g, ".").trim();
}

export function citationInstruction(style: CitationStyle): string {
  if (style === "IEEE") return "IEEE numbered citations, such as [1], placed before final punctuation";
  if (style === "APA 7") return "APA 7 author-date citations, such as (Smith, 2025)";
  if (style === "Harvard") return "Harvard author-date citations, such as (Smith 2025)";
  return "MLA 9 author citations, such as (Smith)";
}

function citationParts(reference: FileReference) {
  const raw = reference.citation.replace(/^\[\d+\]\s*/, "").trim();
  const titleMatch = raw.match(/[“\"]([^”\"]+)[”\"]/);
  const title = titleMatch?.[1]?.replace(/,$/, "") || reference.filename;
  const titleIndex = titleMatch?.index ?? -1;
  const authors = titleIndex >= 0 ? raw.slice(0, titleIndex).replace(/[\s,]+$/, "") : "";
  const remainder = titleIndex >= 0
    ? raw.slice(titleIndex + (titleMatch?.[0].length ?? 0)).replace(/^[\s,]+/, "")
    : raw;
  const year = [...raw.matchAll(/\b(?:19|20)\d{2}\b/g)].at(-1)?.[0] ?? "n.d.";
  const doi = raw.match(/doi:\s*([^\s,]+)[.,]?/i)?.[1]?.replace(/[.,]$/, "") ?? "";
  const source = remainder
    .replace(new RegExp(`\\b${year.replace(".", "\\.")}\\b[,]?`), "")
    .replace(/doi:\s*[^\s,]+[.,]?/i, "")
    .replace(/[\s,.]+$/, "")
    .trim();
  const firstAuthor = authors.split(/,\s+(?:and\s+)?/)[0]?.trim() ?? "";
  const surname = firstAuthor.split(/\s+/).at(-1)?.replace(/[.,]/g, "") || "Anon.";
  return { authors, title, source, year, doi, surname };
}
