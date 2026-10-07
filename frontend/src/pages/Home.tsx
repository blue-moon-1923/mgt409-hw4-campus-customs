import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import type { ProductSummary } from '../types'
import { useReveal } from '../useReveal'

const DEPARTMENTS = [
  {
    title: 'Hoodies & Crewnecks',
    body: 'Fleece weights for a cold walk up Science Hill, from lightweight pullovers to reverse-weave heavyweights.',
  },
  {
    title: 'Tees & Long Sleeves',
    body: 'Soft tri-blends and performance knits carrying shields, bulldogs, and wordmarks.',
  },
  {
    title: 'Residential Colleges',
    body: 'Branford, Saybrook, Pierson, Morse, Davenport, Grace Hopper and the rest, each with its own crest.',
  },
  {
    title: 'Varsity & Club Teams',
    body: 'Left-chest marks for baseball, crew, fencing, sailing, diving, hockey, and more.',
  },
]

export default function Home() {
  const [featured, setFeatured] = useState<ProductSummary[]>([])
  const departmentsRef = useReveal<HTMLUListElement>()
  const featuredRef = useReveal<HTMLElement>()

  useEffect(() => {
    // A quiet failure is fine here: the hero and copy stand on their own, and the
    // products page reports API problems properly.
    fetchProducts()
      .then((products) => setFeatured(products.filter((p) => p.in_stock).slice(0, 4)))
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <p className="eyebrow">New Haven · Since the last reunion weekend</p>
          <h1>
            Gear worth keeping <em>long</em> after graduation.
          </h1>
          <p className="hero-lede">
            Campus Customs prints Yale apparel the way students actually wear it — heavy fleece
            for February, honest cotton for everything else, and crests for every residential
            college and team on campus.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/products">
              Shop the catalogue
            </Link>
            <Link className="button button-ghost" to="/about">
              Our story
            </Link>
          </div>

          <ul className="hero-stats">
            <li>
              <strong>102</strong>
              <span>Designs in stock</span>
            </li>
            <li>
              <strong>XS–XXL</strong>
              <span>Every style, full run</span>
            </li>
            <li>
              <strong>14</strong>
              <span>Residential colleges</span>
            </li>
            <li>
              <strong>1</strong>
              <span>Unbeatable bulldog</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="page page-tight">
        <h2 className="section-title">What we stock</h2>
        <ul className="department-grid" ref={departmentsRef}>
          {DEPARTMENTS.map((department) => (
            <li key={department.title} className="department-card">
              <h3>{department.title}</h3>
              <p>{department.body}</p>
            </li>
          ))}
        </ul>
      </section>

      {featured.length > 0 && (
        <section className="page" ref={featuredRef}>
          <div className="section-head">
            <h2 className="section-title">In stock right now</h2>
            <Link className="text-link" to="/products">
              See all products →
            </Link>
          </div>
          <ul className="product-grid">
            {featured.map((product, index) => (
              <ProductCard key={product.product_id} product={product} index={index} />
            ))}
          </ul>
        </section>
      )}

      <section className="service-band">
        <ul>
          <li>
            <h3>Pick up on campus</h3>
            <p>Order online and collect the same week, no shipping charge.</p>
          </li>
          <li>
            <h3>Six sizes, XS to XXL</h3>
            <p>Every design is cut across the full size run, so teams can order together.</p>
          </li>
          <li>
            <h3>Printed in house</h3>
            <p>Embroidery and screen printing happen a few blocks from the Green.</p>
          </li>
        </ul>
      </section>
    </>
  )
}
