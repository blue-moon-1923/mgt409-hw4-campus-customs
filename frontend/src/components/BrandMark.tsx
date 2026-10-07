/** Campus Customs shield. A monogram beats a text logo for a shop that prints crests. */
export default function BrandMark({ className = '' }: { className?: string }) {
  return (
    <svg
      className={`brand-shield ${className}`}
      viewBox="0 0 40 44"
      role="img"
      aria-label="Campus Customs"
      focusable="false"
    >
      <path
        d="M2 2h36v24c0 8-8 13-18 16C10 39 2 34 2 26V2z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path d="M2 2h36v24c0 8-8 13-18 16C10 39 2 34 2 26V2z" className="brand-shield-inner" />
      <text x="20" y="27" className="brand-shield-letters" textAnchor="middle">
        CC
      </text>
    </svg>
  )
}
