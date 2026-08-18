<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getSalesOrder } from '../api/orderApi'

const route = useRoute()
const order = ref(null)
const isLoading = ref(false)
const loadError = ref('')

const orderName = computed(() => String(route.params.orderName || ''))

function formatDate(value) {
  if (!value) {
    return ''
  }

  return new Intl.DateTimeFormat('en-AE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

function formatCurrency(value, currency = 'AED') {
  return `${currency || 'AED'} ${Number(value || 0).toFixed(2)}`
}

async function loadOrder() {
  if (!orderName.value) {
    return
  }

  isLoading.value = true
  loadError.value = ''
  order.value = null

  try {
    const response = await getSalesOrder(orderName.value)
    order.value = response?.message || null
  } catch (error) {
    loadError.value = error.message || 'Unable to load this order.'
  } finally {
    isLoading.value = false
  }
}

watch(orderName, loadOrder, { immediate: true })
</script>

<template>
  <section class="orders-page">
    <header class="cart-page-header orders-page-header">
      <div>
        <p class="section-label">Order details</p>
        <h1>{{ orderName }}</h1>
      </div>
      <RouterLink class="cart-continue-button" :to="{ name: 'orders' }">
        Back to orders
      </RouterLink>
    </header>

    <p v-if="isLoading" class="dashboard-message">Loading order...</p>
    <p v-if="loadError" class="form-message error-message">{{ loadError }}</p>

    <section v-if="order" class="order-history-card" aria-label="Order summary">
      <header class="order-history-header">
        <div>
          <strong>{{ order.name }}</strong>
          <span>{{ formatDate(order.transaction_date) }}</span>
        </div>
        <span class="order-status-pill">{{ order.status }}</span>
      </header>

      <div class="order-detail-info-grid">
        <div v-if="order.delivery_date" class="order-detail-info-item">
          <span>Delivery date</span>
          <strong>{{ formatDate(order.delivery_date) }}</strong>
        </div>
        <div v-if="order.delivery_slot" class="order-detail-info-item">
          <span>Delivery slot</span>
          <strong>{{ order.delivery_slot }}</strong>
        </div>
        <div v-if="order.shipping_address" class="order-detail-info-item">
          <span>Delivery address</span>
          <strong>{{ order.shipping_address }}</strong>
        </div>
        <div v-if="order.contact_display" class="order-detail-info-item">
          <span>Contact</span>
          <strong>{{ order.contact_display }}<template v-if="order.contact_mobile"> · {{ order.contact_mobile }}</template></strong>
        </div>
      </div>

      <p v-if="order.purchase_orders?.length" class="order-purchase-orders">
        Purchase order {{ order.purchase_orders.join(', ') }}
      </p>

      <div class="order-history-items">
        <article
          v-for="item in order.items"
          :key="item.item_code"
          class="ordered-product-item"
        >
          <img v-if="item.image" class="ordered-product-image" :src="item.image" :alt="item.item_name" />
          <div v-else class="ordered-product-image ordered-product-image-fallback">
            {{ item.item_name.slice(0, 1) }}
          </div>
          <div class="ordered-product-info">
            <h3>{{ item.item_name }}</h3>
            <p>Qty {{ item.qty }} &middot; {{ formatCurrency(item.rate, order.currency) }} each</p>
          </div>
          <strong>{{ formatCurrency(item.amount, order.currency) }}</strong>
        </article>
      </div>

      <div class="order-detail-totals">
        <div class="order-detail-totals-row">
          <span>Subtotal</span>
          <span>{{ formatCurrency(order.net_total, order.currency) }}</span>
        </div>
        <div v-if="order.total_taxes_and_charges" class="order-detail-totals-row">
          <span>Taxes &amp; charges</span>
          <span>{{ formatCurrency(order.total_taxes_and_charges, order.currency) }}</span>
        </div>
        <div class="order-detail-totals-row order-detail-totals-grand">
          <span>Total</span>
          <strong>{{ formatCurrency(order.grand_total, order.currency) }}</strong>
        </div>
      </div>
    </section>
  </section>
</template>
