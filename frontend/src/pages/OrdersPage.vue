<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, hasPersistedPhoneAuthState, restoreLoginSession } from '../api/authApi'
import { getOrderHistory } from '../api/orderHistoryApi'
import { addProductReview } from '../api/reviewApi'
import { clearCurrentUser, currentUser, setCurrentUser } from '../data/authStore'

const router = useRouter()
const orders = ref([])
const isLoadingOrders = ref(false)
const ordersError = ref('')
const STAR_OPTIONS = [1, 2, 3, 4, 5]
const reviewForms = ref({})
const reviewStatusByItem = ref({})
const expandedReviewItems = ref({})

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

function getReviewKey(orderName, itemCode) {
  return `${orderName}::${itemCode}`
}

function isReviewExpanded(orderName, itemCode) {
  return Boolean(expandedReviewItems.value[getReviewKey(orderName, itemCode)])
}

function toggleReviewExpanded(orderName, itemCode) {
  const reviewKey = getReviewKey(orderName, itemCode)
  expandedReviewItems.value[reviewKey] = !expandedReviewItems.value[reviewKey]
}

function getReviewForm(orderName, itemCode) {
  const reviewKey = getReviewKey(orderName, itemCode)

  if (!reviewForms.value[reviewKey]) {
    reviewForms.value[reviewKey] = {
      rating: 5,
      description: '',
    }
  }

  return reviewForms.value[reviewKey]
}

function getReviewStatus(orderName, itemCode) {
  return reviewStatusByItem.value[getReviewKey(orderName, itemCode)] || {
    isSubmitting: false,
    successMessage: '',
    errorMessage: '',
    submittedReview: null,
  }
}

function getSubmittedReview(orderName, item) {
  return (
    getReviewStatus(orderName, item.item_code).submittedReview
    || item.submitted_review
    || null
  )
}

function updateReviewRating(orderName, itemCode, rating) {
  getReviewForm(orderName, itemCode).rating = rating
}

function updateReviewDescription(orderName, itemCode, description) {
  getReviewForm(orderName, itemCode).description = description
}

function getRatingCaption(rating) {
  if (rating >= 5) {
    return 'Excellent'
  }

  if (rating >= 4) {
    return 'Very good'
  }

  if (rating >= 3) {
    return 'Good'
  }

  if (rating >= 2) {
    return 'Fair'
  }

  return 'Poor'
}

async function submitReview(orderName, item) {
  const itemCode = String(item.item_code || '')
  const reviewKey = getReviewKey(orderName, itemCode)
  const form = getReviewForm(orderName, itemCode)

  reviewStatusByItem.value[reviewKey] = {
    isSubmitting: true,
    successMessage: '',
    errorMessage: '',
  }

  try {
    await addProductReview({
      orderName,
      productId: itemCode,
      rating: form.rating,
      description: form.description,
    })
    reviewStatusByItem.value[reviewKey] = {
      isSubmitting: false,
      successMessage: 'Review added successfully.',
      errorMessage: '',
      submittedReview: {
        customerName: currentUser.value?.full_name || currentUser.value?.fullName || currentUser.value?.email || 'You',
        rating: form.rating,
        description: form.description,
      },
    }
    expandedReviewItems.value[reviewKey] = true
    reviewForms.value[reviewKey] = {
      rating: form.rating,
      description: '',
    }
  } catch (error) {
    reviewStatusByItem.value[reviewKey] = {
      isSubmitting: false,
      successMessage: '',
      errorMessage: error.message || 'Unable to add review.',
    }
  }
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

        <div class="order-history-items" @click.stop @keydown.stop>
          <article
            v-for="item in order.items"
            :key="`${order.name}-${item.item_code}`"
            class="ordered-product-item ordered-product-review-item"
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
            <div class="ordered-product-review-body">
              <div class="ordered-product-review-top">
                <div class="ordered-product-info">
                  <h3>{{ item.item_name }}</h3>
                  <p>Qty {{ item.qty }}</p>
                </div>
                <div class="ordered-product-review-actions">
                  <strong>{{ formatCurrency(item.amount, order.currency) }}</strong>
                  <button
                    v-if="!getSubmittedReview(order.name, item)"
                    class="ordered-product-review-toggle"
                    type="button"
                    @click.stop="toggleReviewExpanded(order.name, item.item_code)"
                  >
                    Add review
                  </button>
                </div>
              </div>

              <div
                v-if="getSubmittedReview(order.name, item)"
                class="ordered-product-submitted-review is-inline"
              >
                <div class="ordered-product-submitted-review-header">
                  <span>Submitted review</span>
                  <strong>{{ '★'.repeat(getSubmittedReview(order.name, item).rating) }}</strong>
                </div>
                <p>{{ getSubmittedReview(order.name, item).description }}</p>
              </div>

              <div
                v-if="isReviewExpanded(order.name, item) && !getSubmittedReview(order.name, item)"
                class="ordered-product-review-form"
              >
                <div class="ordered-product-review-field is-wide">
                  <span>Your rating</span>
                  <div class="ordered-product-star-picker" role="radiogroup" aria-label="Choose rating">
                    <button
                      v-for="ratingOption in STAR_OPTIONS"
                      :key="`${order.name}-${item.item_code}-${ratingOption}`"
                      class="ordered-product-star-button"
                      :class="{
                        'is-selected': getReviewForm(order.name, item.item_code).rating >= ratingOption,
                      }"
                      type="button"
                      :aria-label="`${ratingOption} star${ratingOption === 1 ? '' : 's'}`"
                      :aria-pressed="getReviewForm(order.name, item.item_code).rating === ratingOption"
                      @click.stop="updateReviewRating(order.name, item.item_code, ratingOption)"
                    >
                      ★
                    </button>
                    <strong class="ordered-product-star-caption">
                      {{ getRatingCaption(getReviewForm(order.name, item.item_code).rating) }}
                    </strong>
                  </div>
                </div>

                <label class="ordered-product-review-field is-wide">
                  <span>Your review</span>
                  <textarea
                    rows="3"
                    placeholder="Tell customers about product quality, freshness, packaging, or delivery."
                    :value="getReviewForm(order.name, item.item_code).description"
                    @click.stop
                    @input="updateReviewDescription(order.name, item.item_code, $event.target.value)"
                  />
                  <small>Short, clear feedback helps other customers.</small>
                </label>

                <button
                  class="ordered-product-review-submit"
                  type="button"
                  :disabled="getReviewStatus(order.name, item.item_code).isSubmitting"
                  @click.stop="submitReview(order.name, item)"
                >
                  {{ getReviewStatus(order.name, item.item_code).isSubmitting ? 'Saving...' : 'Add review' }}
                </button>
              </div>

              <p
                v-if="getReviewStatus(order.name, item.item_code).successMessage"
                class="ordered-product-review-message is-success"
              >
                {{ getReviewStatus(order.name, item.item_code).successMessage }}
              </p>
              <p
                v-if="getReviewStatus(order.name, item.item_code).errorMessage"
                class="ordered-product-review-message is-error"
              >
                {{ getReviewStatus(order.name, item.item_code).errorMessage }}
              </p>
            </div>
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
