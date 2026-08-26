<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, hasPersistedPhoneAuthState, restoreLoginSession } from '../api/authApi'
import { getCustomerToSupplierDistanceKm, LOCATION_UPDATED_EVENT } from '../api/deliveryEta'
import {
  createCashOnDeliveryOrder,
  createStripeCheckoutSession,
  resumeCheckoutSession,
  syncCartSalesOrder,
  storeCheckoutResumeToken,
} from '../api/paymentApi'
import { customerAddresses } from '../data/addressStore'
import { clearCurrentUser, currentUser, isAuthReady, setCurrentUser } from '../data/authStore'
import { clearCart } from '../data/cartStore'
import {
  cartProducts,
  updateCartProductQuantity,
} from '../data/cartStore'

const emit = defineEmits(['continueShopping', 'login'])
const router = useRouter()

const totalDeliveryDistanceKm = ref(null)
const isDeliveryDistanceLoading = ref(false)
const deliveryFee = computed(() => calculateDeliveryFee(totalDeliveryDistanceKm.value))
const salesOrderName = ref('')
const couponCodeInput = ref('')
const appliedCouponCode = ref('')
const couponDiscountAmount = ref(0)
const couponItemPricing = ref([])
const couponFeedback = ref('')
const couponError = ref('')
const isApplyingCoupon = ref(false)
const originalItemsTotal = computed(() =>
  cartProducts.value.reduce((total, item) => total + getItemLineTotal(item), 0),
)
const discountedItemsTotal = computed(() =>
  cartProducts.value.reduce((total, item, index) => total + getDisplayItemLineTotal(item, index), 0),
)
const hasCouponDiscount = computed(() => couponDiscountAmount.value > 0)
const payableTotal = computed(() =>
  Math.max(discountedItemsTotal.value + deliveryFee.value, 0),
)
const isStartingCheckout = ref(false)
const isPlacingCodOrder = ref(false)
const checkoutError = ref('')
const isAddressRequired = ref(false)
const isAddressExpanded = ref(false)
const fulfillmentMode = ref('delivery')
const selectedDeliverySlot = ref('')
const deliveryDateInput = ref(null)
const isDeliveryDatePickerVisible = ref(false)
const LAST_COD_ORDER_ITEMS_STORAGE_KEY = 'buyInMinutesLastCodOrderItems'
const ALLOWED_DELIVERY_DATES = [
  '2026-08-27',
  '2026-08-28',
  '2026-08-29',
  '2026-08-30',
  '2026-08-31',
]
const deliveryDateMin = ALLOWED_DELIVERY_DATES[0]
const deliveryDateMax = ALLOWED_DELIVERY_DATES[ALLOWED_DELIVERY_DATES.length - 1]
const deliverySlots = [
  '10 AM - 12 PM',
  '12 PM - 2 PM',
  '2 PM - 4 PM',
  '4 PM - 6 PM',
]
const selectedDeliveryDate = ref('')
function itemRequiresDeliverySlot(item) {
  return (
    item?.customDeliverySlots === true
    || item?.customDeliverySlots === 1
    || item?.customDeliverySlots === '1'
    || item?.customDeliverySlots === 'Yes'
    || item?.custom_delivery_slots === true
    || item?.custom_delivery_slots === 1
    || item?.custom_delivery_slots === '1'
    || item?.custom_delivery_slots === 'Yes'
  )
}

const requiresDeliverySlot = computed(() =>
  cartProducts.value.some((item) => itemRequiresDeliverySlot(item)),
)
const effectiveDeliverySlot = computed(() =>
  requiresDeliverySlot.value ? selectedDeliverySlot.value : '',
)
const isCustomerPickup = computed(() => fulfillmentMode.value === 'pickup')
const selectedDeliveryDateContext = computed(() =>
  isCustomerPickup.value ? 'Pickup date' : 'Delivery date',
)
const orderScheduleLabel = computed(() =>
  isCustomerPickup.value ? 'Pickup date' : 'Delivery date',
)
const orderSlotTitle = computed(() =>
  isCustomerPickup.value ? 'Choose pickup slot' : 'Choose delivery slot',
)
const orderSlotDescription = computed(() =>
  isCustomerPickup.value
    ? 'Pick the time slot that works best for pickup.'
    : 'Pick the time window that works best.',
)

const canCheckout = computed(() => isAuthReady.value && Boolean(currentUser.value))
const checkoutButtonLabel = computed(() => {
  if (!isAuthReady.value) {
    return 'Checking session...'
  }

  return canCheckout.value ? '' : 'Login to Proceed'
})
const hasDeliveryAddress = computed(() => customerAddresses.value.length > 0)
const selectedDeliveryDateLabel = computed(() => formatDeliveryDate(selectedDeliveryDate.value))
const deliveryDatePrompt = computed(() =>
  isCustomerPickup.value ? 'Choose pickup date' : 'Choose delivery date',
)
const selectedDeliveryAddress = computed(() =>
  customerAddresses.value.find((address) => address.isDefault)
  || customerAddresses.value[0]
  || null,
)
const selectedDeliveryAddressSummary = computed(() => {
  if (!selectedDeliveryAddress.value) {
    return ''
  }

  return [
    selectedDeliveryAddress.value.area,
    selectedDeliveryAddress.value.building,
    selectedDeliveryAddress.value.street,
    selectedDeliveryAddress.value.emirate,
  ].filter(Boolean).slice(0, 3).join(', ')
})
const totalUnits = computed(() =>
  cartProducts.value.reduce((total, item) => total + Number(item.quantity || 0), 0),
)
const totalLines = computed(() => cartProducts.value.length)
const pickupLocations = computed(() => {
  const locations = []
  const seen = new Set()

  cartProducts.value.forEach((item) => {
    const supplierName = String(item?.supplierName || item?.supplier || '').trim()
    const supplierAddress = String(
      item?.supplierAddress
      || item?.supplierDetails?.customGoogleAddress
      || item?.supplierDetails?.custom_google_address
      || '',
    ).trim()
    const locationKey = `${supplierName}::${supplierAddress}`

    if (!supplierAddress || seen.has(locationKey)) {
      return
    }

    seen.add(locationKey)
    locations.push({
      supplierName: supplierName || 'Pickup location',
      supplierAddress,
    })
  })

  return locations
})
const cartDistanceRefreshKey = computed(() =>
  cartProducts.value
    .map((item) => [item.id, item.quantity, item.price, item.size || ''].join(':'))
    .join('|'),
)
const itemSavings = computed(() =>
  cartProducts.value.reduce((total, item, index) => {
    const displayUnitPrice = getDisplayItemUnitPrice(item, index)

    if (!item.oldPrice || item.oldPrice <= displayUnitPrice) {
      return total
    }

    return total + (item.oldPrice - displayUnitPrice) * item.quantity
  }, 0),
)

function formatDistanceValue(distanceKm) {
  if (!Number.isFinite(distanceKm) || distanceKm <= 0) {
    return ''
  }

  return distanceKm >= 10
    ? distanceKm.toFixed(1).replace(/\.0$/, '')
    : distanceKm.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}

function calculateDeliveryFee(distanceKm) {
  if (!cartProducts.value.length || !Number.isFinite(distanceKm) || distanceKm <= 0) {
    return 0
  }

  const baseDeliveryFee = cartProducts.value.reduce((highestFee, item) => {
    const itemDeliveryFee = Number(item?.customDeliveryFee ?? item?.custom_delivery_fee)

    return Number.isFinite(itemDeliveryFee) && itemDeliveryFee > highestFee
      ? itemDeliveryFee
      : highestFee
  }, 0) || 10
  const roundedDistanceKm = Math.ceil(distanceKm)

  return roundedDistanceKm <= 10
    ? baseDeliveryFee
    : baseDeliveryFee + (roundedDistanceKm - 10)
}

function formatCurrency(value) {
  const amount = Number(value || 0)

  if (!Number.isFinite(amount)) {
    return 'AED 0'
  }

  return `AED ${amount}`
}

function getItemLineTotal(item) {
  return Number(item?.price || 0) * Number(item?.quantity || 0)
}

function getCouponItemPricing(index) {
  return couponItemPricing.value[index] || null
}

function getDisplayItemUnitPrice(item, index) {
  const discountedRate = Number(getCouponItemPricing(index)?.discounted_rate)

  return Number.isFinite(discountedRate) && discountedRate >= 0
    ? discountedRate
    : Number(item?.price || 0)
}

function getDisplayItemLineTotal(item, index) {
  const discountedAmount = Number(getCouponItemPricing(index)?.discounted_amount)

  return Number.isFinite(discountedAmount) && discountedAmount >= 0
    ? discountedAmount
    : getItemLineTotal(item)
}

function getItemCouponDiscount(item, index) {
  const discountAmount = Number(getCouponItemPricing(index)?.discount_amount)

  return Number.isFinite(discountAmount) && discountAmount > 0 ? discountAmount : 0
}

function getItemLineSavings(item, index) {
  const displayUnitPrice = getDisplayItemUnitPrice(item, index)

  if (!item?.oldPrice || Number(item.oldPrice) <= displayUnitPrice) {
    return 0
  }

  return (Number(item.oldPrice) - displayUnitPrice) * Number(item.quantity || 0)
}

function removeCartItem(itemId) {
  updateCartProductQuantity(itemId, 0)
}

function resetCouponState() {
  salesOrderName.value = ''
  appliedCouponCode.value = ''
  couponDiscountAmount.value = 0
  couponItemPricing.value = []
  couponFeedback.value = ''
  couponError.value = ''
}

function updateCouponSummary(syncResponse) {
  salesOrderName.value = syncResponse?.message?.sales_order || salesOrderName.value
  appliedCouponCode.value = syncResponse?.message?.totals?.coupon_code || ''
  couponDiscountAmount.value = Number(syncResponse?.message?.totals?.discount_amount || 0)
  couponItemPricing.value = Array.isArray(syncResponse?.message?.item_pricing)
    ? syncResponse.message.item_pricing
    : []
}

async function syncCouponPreview(couponCode = appliedCouponCode.value, options = {}) {
  if (!canCheckout.value || !cartProducts.value.length) {
    if (!cartProducts.value.length) {
      resetCouponState()
    }
    return null
  }

  const response = await syncCartSalesOrder(
    cartProducts.value,
    salesOrderName.value,
    selectedDeliveryAddress.value,
    selectedDeliveryDate.value,
    effectiveDeliverySlot.value,
    deliveryFee.value,
    couponCode,
    isCustomerPickup.value,
  )

  updateCouponSummary(response)

  if (!couponCode) {
    couponFeedback.value = ''
    couponError.value = ''
    if (!options.keepDraftSalesOrder) {
      salesOrderName.value = response?.message?.sales_order || salesOrderName.value
    }
    return response
  }

  couponFeedback.value = `Coupon ${appliedCouponCode.value} applied.`
  couponError.value = ''
  return response
}

async function applyCouponCode() {
  couponFeedback.value = ''
  couponError.value = ''

  const couponCode = String(couponCodeInput.value || '').trim()
  if (!couponCode) {
    couponError.value = 'Enter a coupon code.'
    return
  }

  if (!(await ensureCheckoutSession())) {
    couponError.value = 'Please login to apply a coupon.'
    return
  }

  isApplyingCoupon.value = true

  try {
    await syncCouponPreview(couponCode)
    couponCodeInput.value = couponCode
  } catch (error) {
    couponDiscountAmount.value = 0
    appliedCouponCode.value = ''
    couponItemPricing.value = []
    couponError.value = error.message || 'Unable to apply coupon.'
  } finally {
    isApplyingCoupon.value = false
  }
}

async function removeCouponCode() {
  couponFeedback.value = ''
  couponError.value = ''
  couponCodeInput.value = ''

  if (!canCheckout.value || !salesOrderName.value) {
    resetCouponState()
    return
  }

  isApplyingCoupon.value = true

  try {
    await syncCouponPreview('')
  } catch (error) {
    couponError.value = error.message || 'Unable to remove coupon.'
  } finally {
    isApplyingCoupon.value = false
  }
}

function getSupplierDistanceKey(item = {}) {
  const latitude = item?.supplierDetails?.customLatitude
    || item?.supplierDetails?.custom_latitude
    || item?.supplierLatitude
    || item?.custom_latitude
    || ''
  const longitude = item?.supplierDetails?.customLongitude
    || item?.supplierDetails?.custom_longitude
    || item?.supplierLongitude
    || item?.custom_longitude
    || ''
  const supplierAddress = String(
    item?.supplierDetails?.customGoogleAddress
      || item?.supplierDetails?.custom_google_address
      || item?.supplierAddress
      || '',
  ).trim().toLowerCase()

  if (latitude && longitude) {
    return `coords:${latitude},${longitude}`
  }

  if (supplierAddress) {
    return `address:${supplierAddress}`
  }

  return `item:${item.id}`
}

let deliveryDistanceRequestId = 0

async function refreshDeliveryDistance() {
  const requestId = ++deliveryDistanceRequestId

  if (!cartProducts.value.length) {
    totalDeliveryDistanceKm.value = null
    isDeliveryDistanceLoading.value = false
    return
  }

  isDeliveryDistanceLoading.value = true

  try {
    const uniqueSupplierItems = Array.from(
      cartProducts.value.reduce((supplierMap, item) => {
        const supplierKey = getSupplierDistanceKey(item)

        if (!supplierMap.has(supplierKey)) {
          supplierMap.set(supplierKey, item)
        }

        return supplierMap
      }, new Map()).values(),
    )
    const distances = await Promise.all(
      uniqueSupplierItems.map((item) => getCustomerToSupplierDistanceKm(item)),
    )

    if (requestId !== deliveryDistanceRequestId) {
      return
    }

    const resolvedDistances = distances.filter((distance) => Number.isFinite(distance) && distance > 0)
    totalDeliveryDistanceKm.value = resolvedDistances.length
      ? resolvedDistances.reduce((total, distance) => total + distance, 0)
      : null
  } catch {
    if (requestId !== deliveryDistanceRequestId) {
      return
    }

    totalDeliveryDistanceKm.value = null
  } finally {
    if (requestId === deliveryDistanceRequestId) {
      isDeliveryDistanceLoading.value = false
    }
  }
}

function selectDeliverySlot(slot) {
  selectedDeliverySlot.value = slot
}

function selectFulfillmentMode(mode) {
  fulfillmentMode.value = mode
}

function openDeliveryDatePicker() {
  isDeliveryDatePickerVisible.value = true
  const input = deliveryDateInput.value

  if (!input) {
    return
  }

  input.focus()

  if (typeof input.showPicker === 'function') {
    input.showPicker()
    return
  }

  input.click()
}

function isAllowedDeliveryDate(dateValue) {
  return ALLOWED_DELIVERY_DATES.includes(dateValue)
}

function normalizeDeliveryDate(dateValue) {
  if (!dateValue) {
    return ''
  }

  return isAllowedDeliveryDate(dateValue) ? dateValue : ''
}

function formatDeliveryDate(dateValue) {
  if (!dateValue) {
    return ''
  }

  const deliveryDate = new Date(`${dateValue}T00:00:00`)

  if (Number.isNaN(deliveryDate.getTime())) {
    return dateValue
  }

  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(deliveryDate)
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
      return true
    }

    const response = await getCurrentUser()
    const message = response?.message || {}

    if (message.is_authenticated) {
      setCurrentUser(message.user)
      return true
    }

    const restoredSession = await restoreLoginSession().catch(() => null)
    const restoredUser = restoredSession?.message?.user

    if (restoredUser) {
      setCurrentUser(restoredUser)
      return true
    }

    clearCurrentUser()
    return false
  } catch (error) {
    console.error('Unable to refresh checkout session', error)

    if (!currentUser.value && !hasPersistedPhoneAuthState()) {
      clearCurrentUser()
    }

    return false
  }
}

async function ensureCheckoutSession() {
  const sessionReady = await refreshCurrentSession()

  if (sessionReady && canCheckout.value) {
    return true
  }

  emit('login')
  return false
}

function isAuthenticationError(error) {
  return /please sign in|authentication|session|login/i.test(error?.message || '')
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

  if (!selectedDeliveryDate.value) {
    checkoutError.value = `Please choose a ${isCustomerPickup.value ? 'pickup' : 'delivery'} date before checkout.`
    return
  }

  if (requiresDeliverySlot.value && !selectedDeliverySlot.value) {
    checkoutError.value = 'Please choose a delivery slot before checkout.'
    return
  }

  isStartingCheckout.value = true

  try {
    console.log('Pay now checkout payload', {
      cartItems: cartProducts.value,
      deliveryAddress: selectedDeliveryAddress.value,
      deliveryDate: selectedDeliveryDate.value,
      deliverySlot: effectiveDeliverySlot.value,
    })
    const response = await createStripeCheckoutSession(
      cartProducts.value,
      '',
      selectedDeliveryAddress.value,
      selectedDeliveryDate.value,
      effectiveDeliverySlot.value,
      deliveryFee.value,
      appliedCouponCode.value,
      isCustomerPickup.value,
    )
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

    if (isAuthenticationError(error)) {
      const sessionRecovered = await refreshCurrentSession()

      if (sessionRecovered && currentUser.value) {
        checkoutError.value = 'Session restored. Please click Pay Now again.'
        return
      }

      if (!hasPersistedPhoneAuthState()) {
        clearCurrentUser()
      }

      emit('login')
      return
    }

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

  if (!selectedDeliveryDate.value) {
    checkoutError.value = `Please choose a ${isCustomerPickup.value ? 'pickup' : 'delivery'} date before placing the order.`
    return
  }

  if (requiresDeliverySlot.value && !selectedDeliverySlot.value) {
    checkoutError.value = 'Please choose a delivery slot before placing the order.'
    return
  }

  isPlacingCodOrder.value = true

  try {
    console.log('Cash on delivery order payload', {
      cartItems: cartProducts.value,
      deliveryAddress: selectedDeliveryAddress.value,
      deliveryDate: selectedDeliveryDate.value,
      deliverySlot: effectiveDeliverySlot.value,
    })
    const response = await createCashOnDeliveryOrder(
      cartProducts.value,
      '',
      selectedDeliveryAddress.value,
      selectedDeliveryDate.value,
      effectiveDeliverySlot.value,
      deliveryFee.value,
      appliedCouponCode.value,
      isCustomerPickup.value,
    )
    console.log('Cash on delivery order response', response)
    const salesOrder = response?.message?.sales_order
    const purchaseOrders = response?.message?.purchase_orders || []
    const orderedItems = cartProducts.value.map((item) => ({
      item_code: item.itemCode || item.id,
      item_name: item.name,
      qty: item.quantity,
      amount: item.price * item.quantity,
      image: item.image,
      size: item.size || '',
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

    if (isAuthenticationError(error)) {
      const sessionRecovered = await refreshCurrentSession()

      if (sessionRecovered && currentUser.value) {
        checkoutError.value = 'Session restored. Please click Cash on Delivery again.'
        return
      }

      if (!hasPersistedPhoneAuthState()) {
        clearCurrentUser()
      }

      emit('login')
      return
    }

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

function goToManageAddresses() {
  router.push({
    name: 'profile',
    query: {
      returnTo: 'cart',
    },
  })
}

function handleWindowFocus() {
  refreshCurrentSession()
}

onMounted(() => {
  refreshCurrentSession()
  refreshDeliveryDistance()
  window.addEventListener('focus', handleWindowFocus)
  window.addEventListener('pageshow', handleWindowFocus)
  window.addEventListener(LOCATION_UPDATED_EVENT, refreshDeliveryDistance)
})

onUnmounted(() => {
  window.removeEventListener('focus', handleWindowFocus)
  window.removeEventListener('pageshow', handleWindowFocus)
  window.removeEventListener(LOCATION_UPDATED_EVENT, refreshDeliveryDistance)
})

watch(
  cartProducts,
  () => {
    refreshDeliveryDistance()
  },
  { deep: true },
)

watch(
  customerAddresses,
  () => {
    refreshDeliveryDistance()
  },
  { deep: true },
)

watch(
  canCheckout,
  (isReady) => {
    if (!isReady) {
      couponCodeInput.value = ''
    }
  },
  { immediate: true },
)

watch(
  selectedDeliveryDate,
  (dateValue) => {
    const normalizedDate = normalizeDeliveryDate(dateValue)

    if (normalizedDate !== dateValue) {
      selectedDeliveryDate.value = normalizedDate
      return
    }

    if (normalizedDate) {
      isDeliveryDatePickerVisible.value = false
    }
  },
  { immediate: true },
)

watch(
  () => [
    cartDistanceRefreshKey.value,
    selectedDeliveryAddress.value?.id || '',
    selectedDeliveryDate.value,
    effectiveDeliverySlot.value,
    deliveryFee.value,
    canCheckout.value,
    appliedCouponCode.value,
  ],
  async (_nextValues, _previousValues) => {
    if (!appliedCouponCode.value || isApplyingCoupon.value) {
      return
    }

    try {
      await syncCouponPreview(appliedCouponCode.value, { keepDraftSalesOrder: true })
    } catch {
      couponDiscountAmount.value = 0
    }
  },
)
</script>

<template>
  <section class="cart-page">
    <header class="cart-page-header">
      <div>
        <p class="section-label">Shopping cart</p>
        <h1>Review your basket</h1>
        <div v-if="cartProducts.length" class="cart-page-insights" aria-label="Cart overview">
          <span class="cart-page-pill">{{ totalLines }} {{ totalLines === 1 ? 'item' : 'items' }}</span>
          <span class="cart-page-pill">{{ totalUnits }} {{ totalUnits === 1 ? 'unit' : 'units' }}</span>
          <span class="cart-page-pill is-highlight">
            {{ isDeliveryDistanceLoading ? 'Checking delivery...' : (deliveryFee ? `${formatCurrency(deliveryFee)} delivery` : 'Free delivery') }}
          </span>
        </div>
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
          v-for="(item, index) in cartProducts"
          :key="item.id"
          class="cart-page-item"
        >
          <img class="cart-page-item-image" :src="item.image" :alt="item.name" />

          <div class="cart-page-item-info">
            <div class="cart-page-item-head">
              <div class="cart-page-item-copy">
                <h2>{{ item.name }}</h2>
                <p v-if="item.size" class="cart-page-item-size">Size: {{ item.size }}</p>
              </div>
            </div>
            <div class="cart-page-item-price">
              <strong>{{ formatCurrency(getDisplayItemUnitPrice(item, index)) }}</strong>
              <span v-if="item.oldPrice && item.oldPrice > getDisplayItemUnitPrice(item, index)">{{ formatCurrency(item.oldPrice) }}</span>
            </div>
            <div class="cart-page-item-meta">
              <span v-if="getItemLineTotal(item) > getDisplayItemLineTotal(item, index)" class="cart-page-item-line-total">
                {{ formatCurrency(getDisplayItemLineTotal(item, index)) }}
                <span>{{ formatCurrency(getItemLineTotal(item)) }}</span>
              </span>
              <span v-if="getItemLineSavings(item, index)" class="cart-page-item-saving">
                Save {{ formatCurrency(getItemLineSavings(item, index)) }}
              </span>
              <span v-if="getItemCouponDiscount(item, index)" class="cart-page-item-saving">
                Coupon -{{ formatCurrency(getItemCouponDiscount(item, index)) }}
              </span>
            </div>
          </div>

          <div class="cart-page-item-actions">
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
          </div>
        </article>
      </section>

      <aside class="cart-summary-panel" aria-label="Order summary">
        <div class="cart-summary-card">
          <div class="cart-summary-heading">
            <div>
              <h2>Order summary</h2>
              <p>Review totals, delivery details, and payment options.</p>
            </div>
            <span class="cart-summary-badge">{{ totalUnits }} {{ totalUnits === 1 ? 'unit' : 'units' }}</span>
          </div>
          <div class="cart-summary-row">
            <span>Items total</span>
            <strong class="cart-summary-amounts">
              <span v-if="hasCouponDiscount" class="cart-summary-original">{{ formatCurrency(originalItemsTotal) }}</span>
              <span>{{ formatCurrency(discountedItemsTotal) }}</span>
            </strong>
          </div>
          <div v-if="itemSavings" class="cart-summary-row cart-summary-saving">
            <span>Savings</span>
            <strong>- {{ formatCurrency(itemSavings) }}</strong>
          </div>
          <div class="cart-summary-row">
            <span>Delivery charge</span>
            <strong>{{ isDeliveryDistanceLoading ? 'Calculating...' : (deliveryFee ? formatCurrency(deliveryFee) : 'FREE') }}</strong>
          </div>
          <div class="cart-summary-total">
            <span>Grand total</span>
            <strong>{{ formatCurrency(payableTotal) }}</strong>
          </div>

          <section class="cart-coupon-card" aria-label="Apply Coupon">
            <div class="cart-coupon-header">
              <h3>Apply Coupon</h3>
            </div>
            <div class="cart-coupon-form">
              <input
                v-model.trim="couponCodeInput"
                class="cart-coupon-input"
                type="text"
                inputmode="text"
                autocomplete="off"
                placeholder="Enter coupon code"
                :disabled="isApplyingCoupon"
              />
              <button
                class="cart-coupon-apply"
                type="button"
                :disabled="isApplyingCoupon || !couponCodeInput.trim()"
                @click="applyCouponCode"
              >
                {{ isApplyingCoupon ? 'Applying...' : 'Apply' }}
              </button>
            </div>
            <div v-if="couponDiscountAmount > 0" class="cart-summary-row cart-summary-saving cart-coupon-discount">
              <span>Coupon discount</span>
              <strong>- {{ formatCurrency(couponDiscountAmount) }}</strong>
            </div>
            <p v-if="couponFeedback" class="cart-coupon-message is-success">
              {{ couponFeedback }}
            </p>
            <p v-if="couponError" class="cart-coupon-message is-error">
              {{ couponError }}
            </p>
          </section>

          <section class="cart-address-card" aria-label="Choose Address">
            <div class="cart-address-header">
              <div>
                <h3>Choose Address</h3>
              </div>
              <button
                class="cart-address-action"
                type="button"
                @click="hasDeliveryAddress ? goToManageAddresses() : goToAddAddress()"
              >
                {{ hasDeliveryAddress ? 'Change' : 'Add address' }}
              </button>
            </div>

            <template v-if="selectedDeliveryAddress">
              <div class="cart-address-body">
                <div class="cart-address-summary-row">
                  <div class="cart-address-summary-copy">
                    <div class="cart-address-badges">
                      <span class="cart-address-label">{{ selectedDeliveryAddress.label }}</span>
                      <span v-if="selectedDeliveryAddress.isDefault" class="cart-address-default">Default</span>
                    </div>
                    <p class="cart-address-line">
                      {{ selectedDeliveryAddress.contactName }}<span v-if="selectedDeliveryAddress.phone"> · {{ selectedDeliveryAddress.phone }}</span>
                    </p>
                    <p v-if="selectedDeliveryAddressSummary" class="cart-address-line">
                      {{ selectedDeliveryAddressSummary }}
                    </p>
                  </div>
                  <button
                    class="cart-address-toggle"
                    type="button"
                    :aria-label="isAddressExpanded ? 'Hide full address' : 'Show full address'"
                    :aria-expanded="isAddressExpanded"
                    @click="isAddressExpanded = !isAddressExpanded"
                  >
                    <svg
                      viewBox="0 0 20 20"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      :class="{ 'is-expanded': isAddressExpanded }"
                      aria-hidden="true"
                    >
                      <path d="M6 8l4 4 4-4" />
                    </svg>
                  </button>
                </div>
                <div v-if="isAddressExpanded" class="cart-address-details">
                  <p v-if="selectedDeliveryAddress.apartmentOfficeName" class="cart-address-line">
                    {{ selectedDeliveryAddress.label === 'Office' ? 'Office name' : 'Apartment name' }}:
                    {{ selectedDeliveryAddress.apartmentOfficeName }}
                  </p>
                  <p v-if="selectedDeliveryAddress.apartmentOfficeNo" class="cart-address-line">
                    {{ selectedDeliveryAddress.label === 'Office' ? 'Office no' : 'Apartment no' }}:
                    {{ selectedDeliveryAddress.apartmentOfficeNo }}
                  </p>
                  <p v-if="selectedDeliveryAddress.building" class="cart-address-line">
                    Building / villa: {{ selectedDeliveryAddress.building }}
                  </p>
                  <p v-if="selectedDeliveryAddress.street" class="cart-address-line">
                    Street: {{ selectedDeliveryAddress.street }}
                  </p>
                  <p v-if="selectedDeliveryAddress.area" class="cart-address-line">
                    Area: {{ selectedDeliveryAddress.area }}
                  </p>
                  <p v-if="selectedDeliveryAddress.landmark" class="cart-address-line">
                    Landmark: {{ selectedDeliveryAddress.landmark }}
                  </p>
                  <p v-if="selectedDeliveryAddress.emirate" class="cart-address-line">
                    Emirate: {{ selectedDeliveryAddress.emirate }}
                  </p>
                </div>
              </div>
            </template>
            <p v-else class="cart-address-empty">
              No saved delivery address found. Add one before checkout.
            </p>
          </section>

          <section class="cart-delivery-options" aria-label="Delivery schedule">
            <div class="cart-fulfillment-mode" role="group" aria-label="Choose how you would like to receive your order">
              <p class="cart-fulfillment-title">How would you like to receive your order?</p>
              <div class="cart-fulfillment-options">
                <button
                  class="cart-fulfillment-option"
                  :class="{ 'is-selected': fulfillmentMode === 'delivery' }"
                  type="button"
                  @click="selectFulfillmentMode('delivery')"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <circle cx="7.5" cy="18" r="1.5" />
                    <circle cx="17.5" cy="18" r="1.5" />
                    <path d="M2.5 4.5h10v9h-10zM12.5 8.5h4l3 3v2h-7zM5 8h3M4 11h2" />
                  </svg>
                  <span>Delivery</span>
                </button>
                <button
                  class="cart-fulfillment-option"
                  :class="{ 'is-selected': fulfillmentMode === 'pickup' }"
                  type="button"
                  @click="selectFulfillmentMode('pickup')"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M5 8.5h14v10H5zM8 8.5V7a4 4 0 0 1 8 0v1.5M9 13h6" />
                  </svg>
                  <span>Customer Pickup</span>
                </button>
              </div>
            </div>

            <div
              v-if="isCustomerPickup && pickupLocations.length"
              class="cart-pickup-location"
              aria-label="Pickup location"
            >
              <div class="cart-pickup-location-header">
                <h3>Pickup Location</h3>
              </div>
              <div class="cart-pickup-location-list">
                <div
                  v-for="location in pickupLocations"
                  :key="`${location.supplierName}-${location.supplierAddress}`"
                  class="cart-pickup-location-item"
                >
                  <strong>{{ location.supplierName }}</strong>
                  <p>{{ location.supplierAddress }}</p>
                </div>
              </div>
            </div>

            <div class="cart-date-picker">
              <label class="cart-date-label" for="cart-delivery-date">{{ orderScheduleLabel }}</label>
              <div class="cart-date-input-shell" @click="openDeliveryDatePicker">
                <div class="cart-date-display">
                  <span class="cart-date-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="5" width="18" height="16" rx="3" />
                      <path d="M16 3v4M8 3v4M3 10h18" />
                    </svg>
                  </span>
                  <div class="cart-date-copy">
                    <span>{{ selectedDeliveryDateContext }}</span>
                    <strong>{{ selectedDeliveryDateLabel || deliveryDatePrompt }}</strong>
                  </div>
                  <span class="cart-date-action" aria-hidden="true">{{ selectedDeliveryDate ? 'Change' : 'Choose' }}</span>
                </div>
                <input
                  v-if="isDeliveryDatePickerVisible"
                  id="cart-delivery-date"
                  ref="deliveryDateInput"
                  v-model="selectedDeliveryDate"
                  class="cart-date-input"
                  type="date"
                  :min="deliveryDateMin"
                  :max="deliveryDateMax"
                  @click="openDeliveryDatePicker"
                  @input="selectedDeliveryDate = normalizeDeliveryDate(selectedDeliveryDate)"
                />
              </div>
            </div>

            <template v-if="requiresDeliverySlot">
              <div class="cart-delivery-heading cart-slot-heading">
                <span class="cart-delivery-step">1</span>
                <div>
                  <h3>{{ orderSlotTitle }}</h3>
                  <p>{{ orderSlotDescription }}</p>
                </div>
              </div>

              <div class="cart-slot-options" role="group" :aria-label="orderSlotTitle">
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
              <p v-if="!selectedDeliverySlot" class="cart-slot-prompt">
                Select a {{ isCustomerPickup ? 'pickup' : 'delivery' }} slot to continue.
              </p>
            </template>

            <p
              v-if="selectedDeliveryDate && effectiveDeliverySlot"
              class="cart-delivery-selection"
            >
              {{ isCustomerPickup ? 'Pickup selected for' : 'Delivery selected for' }}
              <strong>{{ selectedDeliveryDateLabel }}</strong>
              between <strong>{{ effectiveDeliverySlot }}</strong>.
            </p>
            <p
              v-else-if="selectedDeliveryDate"
              class="cart-delivery-selection"
            >
              {{ isCustomerPickup ? 'Pickup date selected for' : 'Delivery date selected for' }} <strong>{{ selectedDeliveryDateLabel }}</strong>.
            </p>
            <label v-if="requiresDeliverySlot" class="visually-hidden" for="cart-delivery-slot">
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
