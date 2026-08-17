<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser } from '../api/authApi'
import {
  createCashOnDeliveryOrder,
  createStripeCheckoutSession,
  resumeCheckoutSession,
  storeCheckoutResumeToken,
} from '../api/paymentApi'
import { customerAddresses } from '../data/addressStore'
import { clearCurrentUser, currentUser, isAuthReady, setCurrentUser } from '../data/authStore'
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
const selectedDeliveryDate = ref('2026-08-26')
const selectedDeliverySlot = ref('')
const LAST_COD_ORDER_ITEMS_STORAGE_KEY = 'buyInMinutesLastCodOrderItems'
const deliveryDateOptions = [
  {
    value: '2026-08-26',
    day: 'Wed',
    date: '26 Aug',
    status: 'Available',
    isAvailable: true,
  },
  {
    value: '2026-08-27',
    day: 'Thurs',
    date: '27 Aug',
    status: 'Full',
    isAvailable: false,
  },
  {
    value: '2026-08-28',
    day: 'Fri',
    date: '28 Aug',
    status: 'Full',
    isAvailable: false,
  },
  {
    value: '2026-08-29',
    day: 'Sat',
    date: '29 Aug',
    status: 'Full',
    isAvailable: false,
  },
]
const deliverySlots = [
  '10 AM - 12 PM',
  '12 PM - 2 PM',
  '2 PM - 4 PM',
  '4 PM - 6 PM',
]
const canCheckout = computed(() => isAuthReady.value && Boolean(currentUser.value))
const checkoutButtonLabel = computed(() => {
  if (!isAuthReady.value) {
    return 'Checking session...'
  }

  return canCheckout.value ? '' : 'Login to Proceed'
})
const hasDeliveryAddress = computed(() => customerAddresses.value.length > 0)
const selectedDeliveryDateLabel = computed(() =>
  deliveryDateOptions.find((dateOption) => dateOption.value === selectedDeliveryDate.value)?.day
  || selectedDeliveryDate.value,
)
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

function selectDeliveryDate(dateOption) {
  if (!dateOption.isAvailable) {
    return
  }

  selectedDeliveryDate.value = dateOption.value
}

function selectDeliverySlot(slot) {
  selectedDeliverySlot.value = slot
}

async function refreshCurrentSession() {
  try {
    let checkoutResumeUser = null

    try {
      const checkoutResumeResponse = await resumeCheckoutSession()
      checkoutResumeUser = checkoutResumeResponse?.message?.user
    } catch (error) {
      console.error('Unable to resume checkout session', error)
    }

    if (checkoutResumeUser) {
      setCurrentUser(checkoutResumeUser)
      return
    }

    const response = await getCurrentUser()
    const message = response?.message || {}

    if (message.is_authenticated) {
      setCurrentUser(message.user)
      return
    }

    clearCurrentUser()
  } catch (error) {
    console.error('Unable to refresh checkout session', error)
  }
}

async function ensureCheckoutSession() {
  if (canCheckout.value) {
    return true
  }

  await refreshCurrentSession()

  if (canCheckout.value) {
    return true
  }

  emit('login')
  return false
}

async function startStripeCheckout() {
  checkoutError.value = ''
  isAddressRequired.value = false

  if (!(await ensureCheckoutSession())) {
    return
  }

  if (!hasDeliveryAddress.value) {
    checkoutError.value = 'Please add a delivery address before checkout.'
    isAddressRequired.value = true
    return
  }

  isStartingCheckout.value = true

  try {
    console.log('Pay now checkout payload', {
      cartItems: cartProducts.value,
      deliveryAddress: selectedDeliveryAddress.value,
    })
    const response = await createStripeCheckoutSession(cartProducts.value, '', selectedDeliveryAddress.value)
    console.log('Pay now checkout response', response)
    const checkoutUrl = response?.message?.checkout_url
    const checkoutResumeToken = response?.message?.checkout_resume_token

    if (!checkoutUrl) {
      throw new Error(response?.message?.message || 'Unable to start checkout.')
    }

    storeCheckoutResumeToken(checkoutResumeToken)
    window.location.assign(checkoutUrl)
  } catch (error) {
    console.error('Pay now checkout failed', error)
    checkoutError.value = error.message
  } finally {
    isStartingCheckout.value = false
  }
}

async function placeCashOnDeliveryOrder() {
  checkoutError.value = ''
  isAddressRequired.value = false

  if (!(await ensureCheckoutSession())) {
    return
  }

  if (!hasDeliveryAddress.value) {
    checkoutError.value = 'Please add a delivery address before checkout.'
    isAddressRequired.value = true
    return
  }

  isPlacingCodOrder.value = true

  try {
    console.log('Cash on delivery order payload', {
      cartItems: cartProducts.value,
      deliveryAddress: selectedDeliveryAddress.value,
    })
    const response = await createCashOnDeliveryOrder(cartProducts.value, '', selectedDeliveryAddress.value)
    console.log('Cash on delivery order response', response)
    const salesOrder = response?.message?.sales_order
    const purchaseOrders = response?.message?.purchase_orders || []
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
        ...(purchaseOrders.length ? { purchase_orders: purchaseOrders.join(',') } : {}),
      },
    })
  } catch (error) {
    console.error('Cash on delivery order failed', error)
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

function handleWindowFocus() {
  refreshCurrentSession()
}

onMounted(() => {
  refreshCurrentSession()
  window.addEventListener('focus', handleWindowFocus)
  window.addEventListener('pageshow', handleWindowFocus)
})

onUnmounted(() => {
  window.removeEventListener('focus', handleWindowFocus)
  window.removeEventListener('pageshow', handleWindowFocus)
})
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

          <section class="cart-delivery-options" aria-label="Delivery schedule">
            <div class="cart-delivery-heading">
              <span class="cart-delivery-step">1</span>
              <div>
                <h3>Choose delivery date</h3>
                <p>Select when you want this order delivered.</p>
              </div>
            </div>

            <div class="cart-date-options" role="group" aria-label="Choose delivery date">
              <button
                v-for="dateOption in deliveryDateOptions"
                :key="dateOption.value"
                class="cart-date-option"
                :class="{
                  'is-selected': selectedDeliveryDate === dateOption.value,
                  'is-full': !dateOption.isAvailable,
                }"
                type="button"
                :disabled="!dateOption.isAvailable"
                @click="selectDeliveryDate(dateOption)"
              >
                <span>{{ dateOption.day }}</span>
                <strong>{{ dateOption.date }}</strong>
                <em>{{ dateOption.status }}</em>
              </button>
            </div>

            <div class="cart-delivery-heading cart-slot-heading">
              <span class="cart-delivery-step">2</span>
              <div>
                <h3>Choose delivery slot</h3>
                <p>Pick the time window that works best.</p>
              </div>
            </div>

            <div class="cart-slot-options" role="group" aria-label="Choose delivery slot">
              <button
                v-for="slot in deliverySlots"
                :key="slot"
                class="cart-slot-option"
                :class="{ 'is-selected': selectedDeliverySlot === slot }"
                type="button"
                @click="selectDeliverySlot(slot)"
              >
                {{ slot }}
              </button>
            </div>

            <p
              v-if="selectedDeliveryDate && selectedDeliverySlot"
              class="cart-delivery-selection"
            >
              Delivery selected for
              <strong>{{ selectedDeliveryDateLabel }}</strong>
              between <strong>{{ selectedDeliverySlot }}</strong>.
            </p>
            <label class="visually-hidden" for="cart-delivery-slot">
              Choose Delivery Slot
              <select id="cart-delivery-slot" v-model="selectedDeliverySlot" tabindex="-1">
                <option value="" disabled>Choose Delivery Slot</option>
                <option
                  v-for="slot in deliverySlots"
                  :key="`select-${slot}`"
                  :value="slot"
                >
                  {{ slot }}
                </option>
              </select>
            </label>
          </section>

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
              :disabled="isPlacingCodOrder || !isAuthReady"
              @click="placeCashOnDeliveryOrder"
            >
              {{ canCheckout ? (isPlacingCodOrder ? 'PLACING ORDER...' : 'CASH ON DELIVERY') : checkoutButtonLabel }}
            </button>
            <button
              class="cart-login-button"
              type="button"
              :disabled="isStartingCheckout || !isAuthReady"
              @click="startStripeCheckout"
            >
              {{ canCheckout ? (isStartingCheckout ? 'PAYING...' : 'PAY NOW') : checkoutButtonLabel }}
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
