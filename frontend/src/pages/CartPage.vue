<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createCashOnDeliveryOrder, createStripeCheckoutSession } from '../api/paymentApi'
import { customerAddresses } from '../data/addressStore'
import { currentUser, isAuthReady } from '../data/authStore'
import { clearCart } from '../data/cartStore'
import {
  cartProducts,
  cartTotal,
  updateCartProductQuantity,
} from '../data/cartStore'

const emit = defineEmits(['continueShopping', 'login'])
const router = useRouter()

const deliveryFee = computed(() => (cartTotal.value >= 60 || !cartProducts.value.length ? 0 : 6))
const payableTotal = computed(() => cartTotal.value + deliveryFee.value)
const isStartingCheckout = ref(false)
const isPlacingCodOrder = ref(false)
const checkoutError = ref('')
const isAddressRequired = ref(false)
const LAST_COD_ORDER_ITEMS_STORAGE_KEY = 'buyInMinutesLastCodOrderItems'
const canCheckout = computed(() => isAuthReady.value && Boolean(currentUser.value))
const hasDeliveryAddress = computed(() => customerAddresses.value.length > 0)
const selectedDeliveryAddress = computed(() =>
  customerAddresses.value.find((address) => address.isDefault)
  || customerAddresses.value[0]
  || null,
)
const itemSavings = computed(() =>
  cartProducts.value.reduce((total, item) => {
    if (!item.oldPrice || item.oldPrice <= item.price) {
      return total
    }

    return total + (item.oldPrice - item.price) * item.quantity
  }, 0),
)

async function startStripeCheckout() {
  checkoutError.value = ''
  isAddressRequired.value = false

  if (!canCheckout.value) {
    emit('login')
    return
  }

  if (!hasDeliveryAddress.value) {
    checkoutError.value = 'Please add a delivery address before checkout.'
    isAddressRequired.value = true
    return
  }

  isStartingCheckout.value = true

  try {
    const response = await createStripeCheckoutSession(cartProducts.value, '', selectedDeliveryAddress.value)
    const checkoutUrl = response?.message?.checkout_url

    if (!checkoutUrl) {
      throw new Error(response?.message?.message || 'Unable to start checkout.')
    }

    window.location.assign(checkoutUrl)
  } catch (error) {
    checkoutError.value = error.message
  } finally {
    isStartingCheckout.value = false
  }
}

async function placeCashOnDeliveryOrder() {
  checkoutError.value = ''
  isAddressRequired.value = false

  if (!canCheckout.value) {
    emit('login')
    return
  }

  if (!hasDeliveryAddress.value) {
    checkoutError.value = 'Please add a delivery address before checkout.'
    isAddressRequired.value = true
    return
  }

  isPlacingCodOrder.value = true

  try {
    const response = await createCashOnDeliveryOrder(cartProducts.value, '', selectedDeliveryAddress.value)
    const salesOrder = response?.message?.sales_order
    const orderedItems = cartProducts.value.map((item) => ({
      item_code: item.itemCode || item.id,
      item_name: item.name,
      qty: item.quantity,
      amount: item.price * item.quantity,
      image: item.image,
    }))

    sessionStorage.setItem(LAST_COD_ORDER_ITEMS_STORAGE_KEY, JSON.stringify(orderedItems))
    clearCart()
    await router.push({
      name: 'payment-success',
      query: {
        method: 'cod',
        ...(salesOrder ? { sales_order: salesOrder } : {}),
      },
    })
  } catch (error) {
    checkoutError.value = error.message
  } finally {
    isPlacingCodOrder.value = false
  }
}

function goToAddAddress() {
  router.push({
    name: 'profile',
    query: {
      openAddress: '1',
      returnTo: 'cart',
    },
  })
}
</script>

<template>
  <section class="cart-page">
    <header class="cart-page-header">
      <div>
        <p class="section-label">Shopping cart</p>
        <h1>Review your basket</h1>
      </div>
      <button
        v-if="cartProducts.length"
        class="cart-continue-button"
        type="button"
        @click="$emit('continueShopping')"
      >
        Continue shopping
      </button>
    </header>

    <div v-if="cartProducts.length" class="cart-page-grid">
      <section class="cart-items-panel" aria-label="Cart items">
        <article
          v-for="item in cartProducts"
          :key="item.id"
          class="cart-page-item"
        >
          <img class="cart-page-item-image" :src="item.image" :alt="item.name" />

          <div class="cart-page-item-info">
            <h2>{{ item.name }}</h2>
            <div class="cart-page-item-price">
              <strong>AED {{ item.price }}</strong>
              <span v-if="item.oldPrice">AED {{ item.oldPrice }}</span>
            </div>
          </div>

          <div class="cart-quantity" :aria-label="`${item.name} quantity`">
            <button
              type="button"
              :aria-label="`Decrease ${item.name} quantity`"
              @click="updateCartProductQuantity(item.id, item.quantity - 1)"
            >
              -
            </button>
            <span>{{ item.quantity }}</span>
            <button
              type="button"
              :aria-label="`Increase ${item.name} quantity`"
              @click="updateCartProductQuantity(item.id, item.quantity + 1)"
            >
              +
            </button>
          </div>
        </article>
      </section>

      <aside class="cart-summary-panel" aria-label="Order summary">
        <div class="cart-summary-card">
          <h2>Order summary</h2>
          <div class="cart-summary-row">
            <span>Items total</span>
            <strong>AED {{ cartTotal }}</strong>
          </div>
          <div v-if="itemSavings" class="cart-summary-row cart-summary-saving">
            <span>Savings</span>
            <strong>- AED {{ itemSavings }}</strong>
          </div>
          <div class="cart-summary-row">
            <span>Delivery charge</span>
            <strong>{{ deliveryFee ? `AED ${deliveryFee}` : 'FREE' }}</strong>
          </div>
          <div class="cart-summary-total">
            <span>Grand total</span>
            <strong>AED {{ payableTotal }}</strong>
          </div>
          <div v-if="checkoutError" class="cart-checkout-message">
            <p class="form-message error-message">
              {{ checkoutError }}
            </p>
            <button
              v-if="isAddressRequired"
              class="cart-add-address-button"
              type="button"
              @click="goToAddAddress"
            >
              Add Address
            </button>
          </div>
          <div class="cart-payment-actions">
            <button
              class="cart-secondary-button"
              type="button"
              :disabled="isPlacingCodOrder"
              @click="placeCashOnDeliveryOrder"
            >
              {{ canCheckout ? (isPlacingCodOrder ? 'PLACING ORDER...' : 'CASH ON DELIVERY') : 'Login to Proceed' }}
            </button>
            <button
              class="cart-login-button"
              type="button"
              :disabled="isStartingCheckout"
              @click="startStripeCheckout"
            >
              {{ canCheckout ? (isStartingCheckout ? 'PAYING...' : 'PAY NOW') : 'Login to Proceed' }}
              <span aria-hidden="true">›</span>
            </button>
          </div>
        </div>

        <section class="cart-policy-card">
          <h2>Cancellation Policy</h2>
          <p>
            Orders cannot be cancelled once packed for delivery. In case of unexpected
            delays, a refund will be provided, if applicable.
          </p>
        </section>
      </aside>
    </div>

    <div v-else class="cart-page-empty">
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
          <circle cx="8" cy="21" r="1" />
          <circle cx="19" cy="21" r="1" />
          <path d="M2 2h3l3 13h10l3-8H7" />
        </svg>
        <span class="empty-cart-dot is-green"></span>
        <span class="empty-cart-dot is-blue"></span>
        <span class="empty-cart-dot is-yellow"></span>
      </div>

      <div class="empty-cart-copy">
        <p class="empty-cart-kicker">Your cart is waiting</p>
        <h2>Add fresh picks to get started</h2>
        <p>
          Browse nearby market items, add what you need, and come back here
          for a quick checkout.
        </p>
      </div>

      <div class="empty-cart-suggestions" aria-label="Shopping suggestions">
        <span>Fresh vegetables</span>
        <span>Dairy essentials</span>
        <span>Meat and fish</span>
      </div>

      <div class="empty-cart-actions" :class="{ 'is-single': currentUser }">
        <button class="primary-dark-button" type="button" @click="$emit('continueShopping')">
          Start shopping
        </button>
        <button
          v-if="!currentUser"
          class="empty-cart-secondary"
          type="button"
          @click="$emit('login')"
        >
          Sign in
        </button>
      </div>
    </div>
  </section>
</template>
