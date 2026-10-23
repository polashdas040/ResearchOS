import React from "react";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

type MarkdownBlock =
  | { type: "code"; language: string; lines: string[] }
  | { type: "lines"; lines: string[] };

export function MarkdownContent({ content, className = "" }: MarkdownContentProps) {
  const blocks = splitCodeBlocks(content);

  return (
    <div className={`space-y-3 leading-7 ${className}`}>
      {blocks.map((block, blockIndex) =>
        block.type === "code" ? (
          <pre key={`code-${blockIndex}`} className="overflow-x-auto rounded bg-[#172026] p-4 text-xs text-white">
            <code data-language={block.language}>{block.lines.join("\n")}</code>
          </pre>
        ) : (
          <MarkdownLines key={`lines-${blockIndex}`} lines={block.lines} />
        )
      )}
    </div>
  );
}

function MarkdownLines({ lines }: { lines: string[] }) {
  const nodes: React.ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (heading) {
      const level = Math.min(heading[1].length, 4);
      const headingClass = level <= 2 ? "text-lg font-semibold" : "text-base font-semibold";
      nodes.push(React.createElement(`h${level}`, { key: `heading-${index}`, className: headingClass }, inlineMarkdown(heading[2])));
      index += 1;
      continue;
    }

    if (isTableHeader(lines, index)) {
      const tableLines: string[] = [lines[index]];
      index += 2;
      while (index < lines.length && /^\s*\|.*\|\s*$/.test(lines[index])) {
        tableLines.push(lines[index]);
        index += 1;
      }
      const rows = tableLines.map(parseTableRow);
      nodes.push(
        <React.Fragment key={`table-${index}`}>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr>{rows[0].map((cell, cellIndex) => <th key={`${cell}-${cellIndex}`} className="border border-[#cfd7df] bg-[#f6f8f9] px-3 py-2 font-semibold">{inlineMarkdown(cell)}</th>)}</tr>
              </thead>
              <tbody>
                {rows.slice(1).map((row, rowIndex) => (
                  <tr key={`row-${rowIndex}`}>{row.map((cell, cellIndex) => <td key={`${cell}-${cellIndex}`} className="border border-[#cfd7df] px-3 py-2">{inlineMarkdown(cell)}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <p
            data-table-trailing-paragraph="true"
            aria-label="Paragraph after table"
            className="min-h-[1.7em] rounded px-1 outline-none hover:bg-[#fbfcfd]"
          ><br /></p>
        </React.Fragment>
      );
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*]\s+/, ""));
        index += 1;
      }
      nodes.push(
        <ul key={`list-${index}`} className="list-disc space-y-1 pl-5">
          {items.map((item, itemIndex) => <li key={`${item}-${itemIndex}`}>{inlineMarkdown(item)}</li>)}
        </ul>
      );
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+\.\s+/, ""));
        index += 1;
      }
      nodes.push(
        <ol key={`ordered-${index}`} className="list-decimal space-y-1 pl-5">
          {items.map((item, itemIndex) => <li key={`${item}-${itemIndex}`}>{inlineMarkdown(item)}</li>)}
        </ol>
      );
      continue;
    }

    nodes.push(<p key={`paragraph-${index}`}>{inlineMarkdown(line)}</p>);
    index += 1;
  }

  return <>{nodes}</>;
}

function inlineMarkdown(text: string) {
  const parts = text.split(/(<span data-image-align="(?:left|center|right)">!\[[^\]]*\]\([^)]+\)<\/span>|<span(?: data-font="[^"]*")?(?: data-size="[^"]*")?>.*?<\/span>|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|~~[^~]+~~|<u>.*?<\/u>|`[^`]+`|\$[^$]+\$|\*[^*]+\*)/g).filter(Boolean);
  return parts.map((part, index) => {
    const alignedImage = /^<span data-image-align="(left|center|right)">!\[([^\]]*)\]\(([^)]+)\)<\/span>$/.exec(part);
    if (alignedImage) {
      const alignmentClass = alignedImage[1] === "center"
        ? "justify-center"
        : alignedImage[1] === "right"
          ? "justify-end"
          : "justify-start";
      return (
        <span key={`${part}-${index}`} data-image-align={alignedImage[1]} className={`my-3 flex w-full ${alignmentClass}`}>
          <img src={alignedImage[3]} alt={alignedImage[2] || "Document image"} className="max-h-[28rem] max-w-full rounded border border-[#d7dde6] object-contain" />
        </span>
      );
    }
    const styledText = /^<span(?: data-font="([^"]*)")?(?: data-size="([^"]*)")?>(.*)<\/span>$/.exec(part);
    if (styledText) {
      return <span key={`${part}-${index}`} style={{ fontFamily: styledText[1] || undefined, fontSize: styledText[2] || undefined }}>{inlineMarkdown(styledText[3])}</span>;
    }
    const image = /^!\[([^\]]*)\]\(([^)]+)\)$/.exec(part);
    if (image) {
      return <img key={`${part}-${index}`} src={image[2]} alt={image[1] || "Document image"} className="my-3 max-h-[28rem] max-w-full rounded border border-[#d7dde6] object-contain" />;
    }
    const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
    if (link) {
      return <a key={`${part}-${index}`} href={link[2]} target="_blank" rel="noreferrer" className="text-[#176b5b] underline">{link[1]}</a>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("~~") && part.endsWith("~~")) {
      return <s key={`${part}-${index}`}>{part.slice(2, -2)}</s>;
    }
    if (part.startsWith("<u>") && part.endsWith("</u>")) {
      return <u key={`${part}-${index}`}>{part.slice(3, -4)}</u>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={`${part}-${index}`} className="rounded bg-[#eef2f5] px-1 py-0.5 text-[0.9em]">{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("$") && part.endsWith("$")) {
      return <span key={`${part}-${index}`} className="inline-flex rounded bg-[#f4f6f8] px-1.5 py-0.5 font-serif italic" aria-label="Equation">{part.slice(1, -1)}</span>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={`${part}-${index}`}>{part.slice(1, -1)}</em>;
    }
    return <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>;
  });
}

function isTableHeader(lines: string[], index: number) {
  return /^\s*\|.*\|\s*$/.test(lines[index] ?? "")
    && /^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$/.test(lines[index + 1] ?? "");
}

function parseTableRow(line: string) {
  return line.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
}

function splitCodeBlocks(content: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = [];
  let lines: string[] = [];
  let codeLines: string[] | null = null;
  let language = "";

  for (const line of content.replace(/\r\n/g, "\n").split("\n")) {
    if (line.trim().startsWith("```")) {
      if (codeLines) {
        blocks.push({ type: "code", language, lines: codeLines });
        codeLines = null;
        language = "";
      } else {
        if (lines.length) blocks.push({ type: "lines", lines });
        lines = [];
        codeLines = [];
        language = line.trim().slice(3);
      }
      continue;
    }
    if (codeLines) codeLines.push(line);
    else lines.push(line);
  }

  if (codeLines) blocks.push({ type: "code", language, lines: codeLines });
  if (lines.length) blocks.push({ type: "lines", lines });
  return blocks;
}
