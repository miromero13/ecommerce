export interface WishlistVariant {
  id: string;
  sku: string;
  size: string | null;
  color: string | null;
  price: number;
  available: number;
}

/** CU16: a favorite garment of the customer. */
export interface WishlistItem {
  id: string;
  product_id: string;
  product_name: string;
  tenant_id: string;
  tenant_name: string | null;
  price: number | null;
  image_url: string | null;
  in_stock: boolean;
  variants: WishlistVariant[];
  created_at: string;
}
