/**
 * Colour dots built from the catalogue's own `colors` list.
 *
 * Shoppers scan for colour before they read anything, and the data was already
 * there as words. Unknown names fall back to a neutral chip with the label, so a
 * new colour never renders as a mystery dot.
 */

const SWATCHES: Record<string, string> = {
  'navy blue': '#1c2a4a',
  navy: '#1c2a4a',
  'royal blue': '#1f4fa3',
  blue: '#2b5fa8',
  'light blue': '#a8c8e4',
  white: '#ffffff',
  ivory: '#f6f1e4',
  cream: '#f2e9d6',
  'heather gray': '#b9bcc0',
  'light gray': '#d2d5d9',
  gray: '#9aa0a6',
  'dark heather gray': '#7b8086',
  'charcoal gray': '#4a4f55',
  'heather charcoal gray': '#5a6066',
  'dark heather charcoal': '#3c4147',
  black: '#17191c',
  red: '#b4242c',
  'dusty coral': '#cf8073',
  green: '#2f6b46',
  yellow: '#e8c33d',
  gold: '#c9a227',
  multicolor:
    'conic-gradient(#b4242c, #e8c33d, #2f6b46, #1f4fa3, #b4242c)',
}

export default function ColorSwatches({
  colors,
  size = 'sm',
}: {
  colors: string[]
  size?: 'sm' | 'lg'
}) {
  if (colors.length === 0) return null

  return (
    <ul className={`swatches swatches-${size}`} aria-label={`Colours: ${colors.join(', ')}`}>
      {colors.map((color) => {
        const value = SWATCHES[color.toLowerCase().trim()]
        if (!value) {
          return (
            <li key={color} className="swatch-chip" title={color}>
              {color}
            </li>
          )
        }
        return (
          <li
            key={color}
            className="swatch"
            title={color}
            style={value.startsWith('conic') ? { background: value } : { backgroundColor: value }}
          >
            <span className="visually-hidden">{color}</span>
          </li>
        )
      })}
    </ul>
  )
}
