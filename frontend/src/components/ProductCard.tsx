import { Link } from 'react-router-dom'

import { formatPrice } from '../api'
import type { CardProduct } from '../types'
import ColorSwatches from './ColorSwatches'

const ALL_SIZES = 6

/** A short, honest line about the size run, when the card has that information. */
function sizeLine(product: CardProduct): string | null {
  const available = product.available_sizes
  if (!available || available.length === 0) return null
  if (available.length >= ALL_SIZES) return 'All sizes'
  return available.join(' · ')
}

export default function ProductCard({
  product,
  index = 0,
}: {
  product: CardProduct
  index?: number
}) {
  const sizes = sizeLine(product)

  return (
    <li
      className="product-card"
      style={{ '--stagger': `${Math.min(index, 11) * 45}ms` } as React.CSSProperties}
    >
      <Link to={`/products/${product.product_id}`} className="product-card-link">
        <div className="product-card-image">
          <img src={product.image_url} alt={product.name} loading="lazy" />
          <span className="product-card-price">{formatPrice(product.price)}</span>
          {!product.in_stock && (
            <span className="product-card-veil">
              <span className="badge">Sold out</span>
            </span>
          )}
        </div>
        <div className="product-card-body">
          <p className="product-card-type">{product.garment_type}</p>
          <h3 className="product-card-name">{product.name}</h3>
          <p className="product-card-blurb">{product.short_description}</p>
          <div className="product-card-foot">
            {product.colors && <ColorSwatches colors={product.colors} />}
            {sizes && <span className="product-card-sizes">{sizes}</span>}
          </div>
        </div>
      </Link>
    </li>
  )
}
