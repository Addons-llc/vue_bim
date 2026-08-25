<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, hasPersistedPhoneAuthState, restoreLoginSession } from '../api/authApi'
import { getOrderHistory } from '../api/orderHistoryApi'
import { clearCurrentUser, currentUser, setCurrentUser } from '../data/authStore'

const router = useRouter()
const orders = ref([])
const isLoadingOrders = ref(false)
const ordersError = ref('')

const hasOrders = computed(() => orders.value.length > 0)

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

async function loadOrders() {
  try {
    const response = await getCurrentUser()
    const message = response?.message || {}

    if (message.is_authenticated) {
      setCurrentUser(message.user)
    } else {
      const restoredSession = await restoreLoginSession().catch(() => null)
      const restoredUser = restoredSession?.message?.user

      if (restoredUser) {
        setCurrentUser(restoredUser)
      } else {
        clearCurrentUser()
      }
    }
  } catch {
    if (!currentUser.value && !hasPersistedPhoneAuthState()) {
      clearCurrentUser()
    }
  }

  if (!currentUser.value) {
    router.replace({ name: 'login' })
    return
  }

  isLoadingOrders.value = true
  ordersError.value = ''

  try {
    const response = await getOrderHistory()
    orders.value = response?.message || []
  } catch (error) {
    orders.value = []
    ordersError.value = error.message || 'Unable to load order history.'
  } finally {
    isLoadingOrders.value = false
  }
}

onMounted(loadOrders)
</script>

<template>
  <section class="orders-page">
    <header class="cart-page-header orders-page-header">
      <div>
        <p class="section-label">Orders</p>
        <h1>Order history</h1>
      </div>
      <RouterLink class="cart-continue-button" :to="{ name: 'home' }">
        Continue shopping
      </RouterLink>
    </header>

    <p v-if="isLoadingOrders" class="dashboard-message">Loading orders...</p>
    <p v-if="ordersError" class="form-message error-message">{{ ordersError }}</p>

    <section v-if="hasOrders" class="orders-list" aria-label="Order history">
      <article
        v-for="order in orders"
        :key="order.name"
        class="order-history-card is-clickable"
        role="button"
        tabindex="0"
        @click="router.push({ name: 'order-details', params: { orderName: order.name } })"
        @keydown.enter="router.push({ name: 'order-details', params: { orderName: order.name } })"
      >
        <header class="order-history-header">
          <div>
            <strong>{{ order.name }}</strong>
            <span>{{ formatDate(order.transaction_date) }}</span>
          </div>
          <span class="order-status-pill">{{ order.status }}</span>
        </header>

        <div class="order-history-meta">
          <span>{{ order.items.length }} item{{ order.items.length === 1 ? '' : 's' }}</span>
          <strong>{{ formatCurrency(order.grand_total, order.currency) }}</strong>
        </div>

        <p v-if="order.purchase_orders?.length" class="order-purchase-orders">
          Purchase order {{ order.purchase_orders.join(', ') }}
        </p>

        <div class="order-history-items">
          <article
            v-for="item in order.items"
            :key="`${order.name}-${item.item_code}`"
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
            <strong>{{ formatCurrency(item.amount, order.currency) }}</strong>
          </article>
        </div>
      </article>
    </section>

    <section v-else-if="!isLoadingOrders && !ordersError" class="cart-page-empty">
      <div class="empty-cart-copy">
        <p class="empty-cart-kicker">No orders</p>
        <h2>Your order history is empty</h2>
        <p>Orders placed from this account will appear here.</p>
      </div>
      <RouterLink class="primary-dark-button" :to="{ name: 'home' }">
        Start shopping
      </RouterLink>
    </section>
  </section>
</template>
