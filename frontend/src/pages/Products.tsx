import { useEffect, useMemo, useState } from 'react'

import { fetchProducts } from '../api'
import { useChat } from '../chat'
import ProductCard from '../components/ProductCard'
import type { ProductSummary } from '../types'

type SortKey = 'name' | 'price-asc' | 'price-desc'

const SORTS: { value: SortKey; label: string }[] = [
  { value: 'name', label: 'Name (A–Z)' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
]

/** Match a query against the words on a card, so "navy crew" narrows sensibly. */
function matches(product: ProductSummary, query: string): boolean {
  if (!query) return true
  const haystack = [
    product.name,
    product.garment_type,
    product.category,
    product.short_description,
    product.colors.join(' '),
  ]
    .join(' ')
    .toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((word) => haystack.includes(word))
}

export default function Products() {
  const { results, clearResults, setIsOpen } = useChat()
  const [products, setProducts] = useState<ProductSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [sort, setSort] = useState<SortKey>('name')
  const [inStockOnly, setInStockOnly] = useState(false)

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((cause: Error) => setError(cause.message))
  }, [])

  const categories = useMemo(() => {
    const counts = new Map<string, number>()
    for (const product of products ?? []) {
      counts.set(product.category, (counts.get(product.category) ?? 0) + 1)
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1])
  }, [products])

  const visible = useMemo(() => {
    const filtered = (products ?? []).filter(
      (product) =>
        (category === 'All' || product.category === category) &&
        (!inStockOnly || product.in_stock) &&
        matches(product, query.trim()),
    )
    const sorted = [...filtered]
    if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
    else if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
    else sorted.sort((a, b) => a.name.localeCompare(b.name))
    return sorted
  }, [products, category, inStockOnly, query, sort])

  const isFiltered = query.trim() !== '' || category !== 'All' || inStockOnly || sort !== 'name'

  function clearFilters() {
    setQuery('')
    setCategory('All')
    setSort('name')
    setInStockOnly(false)
  }

  // A chat answer replaces the grid with just its matches, until it is cleared.
  if (results) {
    return (
      <section className="page">
        <div className="results-banner">
          <div>
            <p className="eyebrow">From the shop assistant</p>
            <h1>{results.heading}</h1>
            <p className="results-query">You asked: “{results.query}”</p>
          </div>
          <div className="results-actions">
            <button type="button" className="button button-ghost" onClick={() => setIsOpen(true)}>
              Reopen chat
            </button>
            <button type="button" className="button button-primary" onClick={clearResults}>
              Show all products
            </button>
          </div>
        </div>

        <p className="count results-count">
          {results.products.length} {results.products.length === 1 ? 'product' : 'products'}
        </p>

        <ul className="product-grid">
          {results.products.map((product, index) => (
            <ProductCard key={product.product_id} product={product} index={index} />
          ))}
        </ul>
      </section>
    )
  }

  if (error) {
    return (
      <section className="page narrow">
        <h1>Products</h1>
        <p className="notice notice-error">{error}</p>
      </section>
    )
  }

  if (products === null) {
    return (
      <section className="page narrow">
        <h1>Products</h1>
        <p className="notice">Loading the catalogue…</p>
      </section>
    )
  }

  return (
    <section className="page">
      <div className="section-head">
        <div>
          <p className="eyebrow">The catalogue</p>
          <h1>Products</h1>
        </div>
        <p className="count">
          {visible.length === products.length
            ? `${products.length} designs`
            : `${visible.length} of ${products.length}`}
        </p>
      </div>

      <div className="toolbar" role="search">
        <div className="toolbar-field toolbar-search">
          <label htmlFor="product-search">Search</label>
          <input
            id="product-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="navy hoodie, bulldog, Saybrook…"
            autoComplete="off"
          />
        </div>

        <div className="toolbar-field">
          <label htmlFor="product-category">Category</label>
          <select
            id="product-category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="All">All ({products.length})</option>
            {categories.map(([name, count]) => (
              <option key={name} value={name}>
                {name} ({count})
              </option>
            ))}
          </select>
        </div>

        <div className="toolbar-field">
          <label htmlFor="product-sort">Sort by</label>
          <select
            id="product-sort"
            value={sort}
            onChange={(event) => setSort(event.target.value as SortKey)}
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <label className="toolbar-toggle">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(event) => setInStockOnly(event.target.checked)}
          />
          In stock only
        </label>

        {isFiltered && (
          <button type="button" className="toolbar-clear" onClick={clearFilters}>
            Clear
          </button>
        )}
      </div>

      {visible.length === 0 ? (
        <p className="notice">
          Nothing matches those filters. Try fewer words, or{' '}
          <button type="button" className="link-button" onClick={clearFilters}>
            clear the filters
          </button>
          .
        </p>
      ) : (
        <ul className="product-grid">
          {visible.map((product, index) => (
            <ProductCard key={product.product_id} product={product} index={index} />
          ))}
        </ul>
      )}
    </section>
  )
}
