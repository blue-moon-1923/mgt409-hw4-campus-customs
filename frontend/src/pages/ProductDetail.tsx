import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { fetchProduct, fetchRelated, formatPrice } from '../api'
import ColorSwatches from '../components/ColorSwatches'
import ProductCard from '../components/ProductCard'
import type { ProductDetail, ProductSummary, StockStatus } from '../types'

const STOCK_LABEL: Record<StockStatus, string> = {
  in_stock: 'In stock',
  low_stock: 'Low stock',
  out_of_stock: 'Sold out',
}

export default function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [chosenSize, setChosenSize] = useState<string | null>(null)
  const [related, setRelated] = useState<ProductSummary[]>([])

  useEffect(() => {
    if (!productId) return
    setProduct(null)
    setError(null)
    setChosenSize(null)
    setRelated([])
    fetchProduct(productId)
      .then(setProduct)
      .catch((cause: Error) => setError(cause.message))
    // A quiet failure is right here: the row is a bonus, not the page.
    fetchRelated(productId)
      .then(setRelated)
      .catch(() => setRelated([]))
  }, [productId])

  if (error) {
    return (
      <section className="page narrow">
        <p className="notice notice-error">{error}</p>
        <Link className="text-link" to="/products">
          ← Back to all products
        </Link>
      </section>
    )
  }

  if (!product) {
    return (
      <section className="page narrow">
        <p className="notice">Loading product…</p>
      </section>
    )
  }

  const selected = product.sizes.find((size) => size.size === chosenSize)

  return (
    <section className="page">
      <Link className="text-link back-link" to="/products">
        ← Back to all products
      </Link>

      <div className="detail-layout">
        <div className="detail-media">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-copy">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>

          <p className="detail-description">{product.description}</p>

          <dl className="detail-facts">
            <div>
              <dt>Colours</dt>
              <dd className="colours">
                <ColorSwatches colors={product.colors} size="lg" />
                {product.colors.join(', ')}
              </dd>
            </div>
            <div>
              <dt>Availability</dt>
              <dd>
                {product.total_quantity > 0
                  ? `${product.available_sizes.length} of ${product.sizes.length} sizes available`
                  : 'Currently sold out'}
              </dd>
            </div>
          </dl>

          <div className="size-block">
            <h2 className="size-heading">Sizes</h2>
            <ul className="size-list">
              {product.sizes.map((size) => {
                const soldOut = size.quantity === 0
                return (
                  <li key={size.size}>
                    <button
                      type="button"
                      className={`size-button${chosenSize === size.size ? ' is-selected' : ''}`}
                      onClick={() => setChosenSize(size.size)}
                      disabled={soldOut}
                      aria-label={`Size ${size.size}, ${STOCK_LABEL[size.status].toLowerCase()}`}
                    >
                      {size.size}
                    </button>
                  </li>
                )
              })}
            </ul>
            <p className="size-hint" aria-live="polite">
              {selected
                ? `${selected.size} — ${STOCK_LABEL[selected.status]}${
                    selected.quantity > 0 ? ` (${selected.quantity} on hand)` : ''
                  }`
                : 'Select a size to see what is on hand. Greyed-out sizes are sold out.'}
            </p>
          </div>

          {product.search_tags.length > 0 && (
            <ul className="tag-list" aria-label="Product tags">
              {product.search_tags.map((tag) => (
                <li key={tag} className="tag">
                  {tag}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {related.length > 0 && (
        <section className="related" aria-label="More like this">
          <div className="section-head">
            <div>
              <p className="eyebrow">Keep looking</p>
              <h2 className="section-title">More {product.category.toLowerCase()}</h2>
            </div>
          </div>
          <ul className="product-grid">
            {related.map((item, index) => (
              <ProductCard key={item.product_id} product={item} index={index} />
            ))}
          </ul>
        </section>
      )}
    </section>
  )
}
