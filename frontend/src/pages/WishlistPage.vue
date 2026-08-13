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
      <p class="section-support">{{ wishlistProducts.length }} saved items</p>
    </div>

    <p v-if="!wishlistProducts.length" class="dashboard-message">
      Your wishlist is empty.
    </p>

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
