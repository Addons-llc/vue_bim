<script setup>
import { useRouter } from 'vue-router'
import ProductCard from '../components/product/ProductCard.vue'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'
import { wishlistProducts } from '../data/wishlistStore'

const router = useRouter()

function openProductDetails(product) {
  const supplierName = product.supplierName || product.supplier || 'Supplier not set'

  saveSelectedProduct(product)
  saveSelectedSupplier({
    name: supplierName,
    details: product.supplierDetails,
    product,
    products: wishlistProducts.value.filter((item) =>
      (item.supplierName || item.supplier || 'Supplier not set') === supplierName,
    ),
  })

  router.push({
    name: 'product-details',
    params: { productId: product.id },
  })
}
</script>

<template>
  <section class="wishlist-page">
    <div class="section-heading">
      <h2>Wishlist</h2>
    </div>

    <section v-if="!wishlistProducts.length" class="cart-page-empty wishlist-empty">
      <div class="empty-cart-visual" aria-hidden="true">
        <svg
          class="empty-cart-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z" />        </svg>
        <span class="empty-cart-dot is-green"></span>
        <span class="empty-cart-dot is-blue"></span>
        <span class="empty-cart-dot is-yellow"></span>
      </div>

      <div class="empty-cart-copy">
        <p class="empty-cart-kicker">Nothing saved yet</p>
        <h2>Your wishlist is empty</h2>
        <p>
          Tap the heart on any product to save it here, so you can find it
          quickly and add it to your cart later.
        </p>
      </div>

      <nav class="empty-cart-suggestions" aria-label="Shopping suggestions">
        <RouterLink :to="{ name: 'categories' }">Categories</RouterLink>
        <RouterLink :to="{ name: 'stores' }">Stores</RouterLink>
        <RouterLink :to="{ name: 'brands' }">Brands</RouterLink>
      </nav>

      <div class="empty-cart-actions is-single">
        <RouterLink class="primary-dark-button" :to="{ name: 'home' }">
          Start shopping
        </RouterLink>
      </div>
    </section>

    <div v-else class="product-grid">
      <ProductCard
        v-for="product in wishlistProducts"
        :key="product.id"
        :product="product"
        @select="openProductDetails"
      />
    </div>
  </section>
</template>
