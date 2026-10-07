export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock'

export interface SizeAvailability {
  size: string
  quantity: number
  status: StockStatus
}

export interface ProductSummary {
  product_id: string
  name: string
  garment_type: string
  category: string
  price: number
  short_description: string
  colors: string[]
  image_url: string
  in_stock: boolean
}

export interface ProductDetail extends ProductSummary {
  description: string
  search_tags: string[]
  sizes: SizeAvailability[]
  available_sizes: string[]
  total_quantity: number
}

export interface PublicUser {
  id: number
  first_name: string | null
  last_name: string | null
  email: string
  created_at: string
}

export interface SignupFields {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export interface ChatProductCard {
  product_id: string
  name: string
  garment_type: string
  category: string
  price: number
  image_url: string
  short_description: string
  in_stock: boolean
  colors: string[]
  available_sizes: string[]
  sold_out_sizes: string[]
}

/** The shape <ProductCard> needs. Both ProductSummary and ChatProductCard satisfy it. */
export interface CardProduct {
  product_id: string
  name: string
  garment_type: string
  category?: string
  price: number
  short_description: string
  image_url: string
  in_stock: boolean
  colors?: string[]
  available_sizes?: string[]
  sold_out_sizes?: string[]
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  products: ChatProductCard[]
  results_heading: string
  tools_used: string[]
}

export interface PageContext {
  path: string
  product_id?: string | null
  results_heading?: string | null
}

export interface StoredChatMessage {
  role: 'user' | 'assistant'
  content: string
  products: ChatProductCard[]
  created_at: string
}

export interface ChatHistoryResponse {
  messages: StoredChatMessage[]
}
