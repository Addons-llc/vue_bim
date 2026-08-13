<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getSalesOrder } from '../api/orderApi'
import { finalizeStripeCheckout } from '../api/paymentApi'
import { clearCart } from '../data/cartStore'

const route = useRoute()
const paymentMethod = computed(() => (route.query.method === 'cod' ? 'cod' : 'stripe'))
const title = computed(() =>
  paymentMethod.value === 'cod' ? 'Order placed successfully' : 'Order payment received',
)
const label = computed(() =>
  paymentMethod.value === 'cod' ? 'Cash on Delivery' : 'Payment confirmed',
)
const message = computed(() =>
  paymentMethod.value === 'cod'
    ? 'Your order has been placed for cash on delivery.'
    : 'Your payment was completed successfully.',
)
const referenceLabel = computed(() =>
  paymentMethod.value === 'cod' ? 'Sales order' : 'Session',
)
const stripeSessionId = computed(() => {
  const value = route.query.session_id
  return Array.isArray(value) ? value[0] : value || ''
})
const referenceValue = computed(() => route.query.sales_order || stripeSessionId.value || '')
const finalizeError = ref('')
const salesOrderName = ref(Array.isArray(route.query.sales_order) ? route.query.sales_order[0] : route.query.sales_order || '')
const orderedProducts = ref([])
const orderedProductsError = ref('')
const isLoadingOrderedProducts = ref(false)
const LAST_COD_ORDER_ITEMS_STORAGE_KEY = 'buyInMinutesLastCodOrderItems'

function loadStoredCodOrderItems() {
  try {
    return JSON.parse(sessionStorage.getItem(LAST_COD_ORDER_ITEMS_STORAGE_KEY)) || []
  } catch {
    return []
  }
}

async function loadOrderedProducts() {
  if (paymentMethod.value === 'cod') {
    orderedProducts.value = loadStoredCodOrderItems()
    sessionStorage.removeItem(LAST_COD_ORDER_ITEMS_STORAGE_KEY)
    return
  }

  if (!salesOrderName.value) {
    return
  }

  isLoadingOrderedProducts.value = true
  orderedProductsError.value = ''

  try {
    const response = await getSalesOrder(salesOrderName.value)
    orderedProducts.value = response?.message?.items || []
  } catch (error) {
    orderedProducts.value = []
    orderedProductsError.value = error.message || 'Unable to load ordered products.'
  } finally {
    isLoadingOrderedProducts.value = false
  }
}

onMounted(async () => {
  if (paymentMethod.value === 'stripe' && stripeSessionId.value) {
    try {
      const response = await finalizeStripeCheckout(stripeSessionId.value)
      salesOrderName.value = response?.message?.sales_order || salesOrderName.value
      orderedProducts.value = response?.message?.items || []
    } catch (error) {
      finalizeError.value = error.message
      return
    }
  }

  if (!orderedProducts.value.length) {
    await loadOrderedProducts()
  }
  clearCart()
})
</script>

<template>
  <section class="payment-result-page">
    <div class="payment-result-panel">
      <p class="section-label">{{ label }}</p>
      <h1>{{ title }}</h1>
      <p>
        {{ message }}
      </p>
      <p v-if="referenceValue && paymentMethod !== 'cod'" class="payment-session-id">
        {{ referenceLabel }} {{ referenceValue }}
      </p>
      <p v-if="finalizeError" class="form-message error-message">
        {{ finalizeError }}
      </p>
      <section
        v-if="isLoadingOrderedProducts || orderedProducts.length || orderedProductsError"
        class="ordered-products-panel"
        aria-label="Ordered products"
      >
        <h2>Ordered products</h2>
        <p v-if="isLoadingOrderedProducts" class="dashboard-message">Loading ordered products...</p>
        <p v-if="orderedProductsError" class="form-message error-message">
          {{ orderedProductsError }}
        </p>
        <div v-if="orderedProducts.length" class="ordered-products-list">
          <article
            v-for="item in orderedProducts"
            :key="item.item_code"
            class="ordered-product-item"
          >
            <img
              v-if="item.image"
              class="ordered-product-image"
              :src="item.image"
              :alt="item.item_name"
            />
            <div v-else class="ordered-product-image ordered-product-image-fallback">
              {{ item.item_name.slice(0, 1) }}
            </div>
            <div class="ordered-product-info">
              <h3>{{ item.item_name }}</h3>
              <p>Qty {{ item.qty }}</p>
            </div>
            <strong>AED {{ item.amount }}</strong>
          </article>
        </div>
      </section>
      <RouterLink class="continue-shopping-button" :to="{ name: 'home' }">
        <svg
          class="continue-shopping-icon"
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="8" cy="21" r="1" />
          <circle cx="19" cy="21" r="1" />
          <path d="M2 2h3l3 13h10l3-8H7" />
        </svg>
        Continue shopping
      </RouterLink>
    </div>
  </section>
</template>
