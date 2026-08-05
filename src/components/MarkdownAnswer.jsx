import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

function CopyButton({ text, label = "Copy answer" }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text || "");
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={copied ? "Copied to clipboard" : label}
      className="rounded-xl bg-slate-100 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function CodeBlock({ inline, className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || "");
  const code = String(children).replace(/\n$/, "");

  if (inline) {
    return (
      <code
        className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-sm text-rose-700"
        {...props}
      >
        {children}
      </code>
    );
  }

  return (
    <div className="group relative my-3 overflow-hidden rounded-xl border border-slate-200 bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {match?.[1] || "code"}
        </span>
        <CopyButton text={code} label="Copy code block" />
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-6 text-slate-100">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

function MarkdownAnswer({ content, showCopy = true, className = "" }) {
  const text = content || "";

  if (!text.trim()) {
    return (
      <p className="text-sm text-slate-500">No content available.</p>
    );
  }

  return (
    <div className={className}>
      {showCopy ? (
        <div className="mb-3 flex justify-end">
          <CopyButton text={text} />
        </div>
      ) : null}
      <div className="markdown-answer prose prose-slate max-w-none text-base leading-7 text-slate-700 sm:text-lg sm:leading-8">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            code: CodeBlock,
            table: ({ children }) => (
              <div className="my-4 overflow-x-auto rounded-xl border border-slate-200">
                <table className="min-w-full border-collapse text-left text-sm">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="border-b border-slate-200 bg-slate-50 px-3 py-2 font-semibold text-slate-800">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border-b border-slate-100 px-3 py-2 text-slate-700">
                {children}
              </td>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                className="font-medium text-sky-700 underline underline-offset-2"
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            ),
          }}
        >
          {text}
        </ReactMarkdown>
      </div>
    </div>
  );
}

export default MarkdownAnswer;
