<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getSalesOrder } from '../api/orderApi'
import { addProductReview } from '../api/reviewApi'

const route = useRoute()
const order = ref(null)
const isLoading = ref(false)
const loadError = ref('')
const reviewForms = ref({})
const reviewStatusByItem = ref({})

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

function getReviewForm(itemCode) {
  if (!reviewForms.value[itemCode]) {
    reviewForms.value[itemCode] = {
      rating: 5,
      description: '',
    }
  }

  return reviewForms.value[itemCode]
}

function getReviewStatus(itemCode) {
  return reviewStatusByItem.value[itemCode] || {
    isSubmitting: false,
    successMessage: '',
    errorMessage: '',
  }
}

function updateReviewRating(itemCode, rating) {
  getReviewForm(itemCode).rating = rating
}

function updateReviewDescription(itemCode, description) {
  getReviewForm(itemCode).description = description
}

async function submitReview(item) {
  const itemCode = String(item.item_code || '')
  const form = getReviewForm(itemCode)

  reviewStatusByItem.value[itemCode] = {
    isSubmitting: true,
    successMessage: '',
    errorMessage: '',
  }

  try {
    await addProductReview({
      orderName: order.value?.name || orderName.value,
      productId: itemCode,
      rating: form.rating,
      description: form.description,
    })
    reviewStatusByItem.value[itemCode] = {
      isSubmitting: false,
      successMessage: 'Review added successfully.',
      errorMessage: '',
    }
    reviewForms.value[itemCode] = {
      rating: form.rating,
      description: '',
    }
  } catch (error) {
    reviewStatusByItem.value[itemCode] = {
      isSubmitting: false,
      successMessage: '',
      errorMessage: error.message || 'Unable to add review.',
    }
  }
}

async function loadOrder() {
  if (!orderName.value) {
    return
  }

  isLoading.value = true
  loadError.value = ''
  order.value = null
  reviewForms.value = {}
  reviewStatusByItem.value = {}

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
          class="ordered-product-item ordered-product-review-item"
        >
          <img v-if="item.image" class="ordered-product-image" :src="item.image" :alt="item.item_name" />
          <div v-else class="ordered-product-image ordered-product-image-fallback">
            {{ item.item_name.slice(0, 1) }}
          </div>
          <div class="ordered-product-review-body">
            <div class="ordered-product-review-top">
              <div class="ordered-product-info">
                <h3>{{ item.item_name }}</h3>
                <p>Qty {{ item.qty }} &middot; {{ formatCurrency(item.rate, order.currency) }} each</p>
              </div>
              <strong>{{ formatCurrency(item.amount, order.currency) }}</strong>
            </div>

            <div class="ordered-product-review-form">
              <label class="ordered-product-review-field">
                <span>Rating</span>
                <select
                  :value="getReviewForm(item.item_code).rating"
                  @change="updateReviewRating(item.item_code, Number($event.target.value))"
                >
                  <option :value="5">5 Stars</option>
                  <option :value="4">4 Stars</option>
                  <option :value="3">3 Stars</option>
                  <option :value="2">2 Stars</option>
                  <option :value="1">1 Star</option>
                </select>
              </label>

              <label class="ordered-product-review-field is-wide">
                <span>Review description</span>
                <textarea
                  rows="3"
                  placeholder="Write your review"
                  :value="getReviewForm(item.item_code).description"
                  @input="updateReviewDescription(item.item_code, $event.target.value)"
                />
              </label>

              <button
                class="ordered-product-review-submit"
                type="button"
                :disabled="getReviewStatus(item.item_code).isSubmitting"
                @click="submitReview(item)"
              >
                {{ getReviewStatus(item.item_code).isSubmitting ? 'Saving...' : 'Add review' }}
              </button>

              <p
                v-if="getReviewStatus(item.item_code).successMessage"
                class="ordered-product-review-message is-success"
              >
                {{ getReviewStatus(item.item_code).successMessage }}
              </p>
              <p
                v-if="getReviewStatus(item.item_code).errorMessage"
                class="ordered-product-review-message is-error"
              >
                {{ getReviewStatus(item.item_code).errorMessage }}
              </p>
            </div>
          </div>
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
