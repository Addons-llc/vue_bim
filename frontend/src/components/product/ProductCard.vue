<script setup>
import { computed, ref, watch } from 'vue'
import { deliveryLocationVersion, getEstimatedDeliveryTimeLabel } from '../../api/deliveryEta'
import {
  addProductToCart,
  cartQuantityById,
  updateCartProductQuantity,
} from '../../data/cartStore'
import {
  isProductWishlisted,
  toggleProductWishlist,
} from '../../data/wishlistStore'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['select'])

const LOW_STOCK_THRESHOLD = 5
const productPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`
const priceFormatter = new Intl.NumberFormat('en-AE', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

const cartQuantity = computed(() => cartQuantityById.value.get(props.product.id) || 0)
const isWishlisted = computed(() => isProductWishlisted(props.product.id))
const isRfqOnly = computed(() => props.product.customRfqOnly === true)
const availableQuantity = computed(() => {
  const quantity = Number(props.product.customAvailableQty ?? props.product.stockQuantity ?? 0)

  return Number.isFinite(quantity) ? quantity : 0
})
const isOutOfStock = computed(() => props.product.inStock === false)
const isLowStock = computed(() =>
  !isOutOfStock.value && availableQuantity.value > 0 && availableQuantity.value <= LOW_STOCK_THRESHOLD,
)
const stockLabel = computed(() => {
  if (isOutOfStock.value) {
    return 'Out of stock'
  }

  if (isLowStock.value) {
    return `Only ${availableQuantity.value} left`
  }

  return availableQuantity.value > 0 ? `${availableQuantity.value} in stock` : 'In stock'
})
// Only cap the quantity when the stock is actually tracked; RFQ items are never capped.
const canIncreaseQuantity = computed(() =>
  isRfqOnly.value || availableQuantity.value <= 0 || cartQuantity.value < availableQuantity.value,
)
const formattedPrice = computed(() => {
  const price = Number(props.product.price)

  return Number.isFinite(price) ? priceFormatter.format(price) : props.product.price
})
const supplierName = computed(() =>
  props.product.supplierName || props.product.supplier || '',
)
const rating = computed(() => Number(props.product.rating) || 0)
const reviewCount = computed(() => Number(props.product.reviewCount) || 0)
const hasRating = computed(() => rating.value > 0 || reviewCount.value > 0)
const reviewLabel = computed(() => (reviewCount.value === 1 ? '1 review' : `${reviewCount.value} reviews`))
const defaultProductSize = computed(() => {
  const rawSize = props.product.selectedSize || props.product.size || props.product.customSize || props.product.custom_size || ''

  if (Array.isArray(rawSize)) {
    return rawSize.map((size) => String(size).trim()).find(Boolean) || ''
  }

  return String(rawSize)
    .split(/\r?\n|[|,;/]+/)
    .map((size) => size.trim())
    .find(Boolean) || String(rawSize).trim()
})
const deliveryTimeLabel = ref(props.product.deliveryTime || '')

let deliveryRequestId = 0

async function updateDeliveryTimeLabel() {
  // Ignore responses from older requests so a slow lookup can't overwrite a newer one.
  const requestId = ++deliveryRequestId
  const label = await getEstimatedDeliveryTimeLabel(props.product)

  if (requestId === deliveryRequestId) {
    deliveryTimeLabel.value = label
  }
}

function handleAddToCart() {
  if (isOutOfStock.value && !isRfqOnly.value) {
    return
  }

  addProductToCart({
    ...props.product,
    selectedSize: defaultProductSize.value,
  })
}

function increaseCartQuantity() {
  if (canIncreaseQuantity.value) {
    handleAddToCart()
  }
}

function decreaseCartQuantity() {
  updateCartProductQuantity(props.product.id, cartQuantity.value - 1)
}

function handleWishlistToggle() {
  toggleProductWishlist(props.product)
}

function selectProduct() {
  emit('select', props.product)
}

function showPlaceholderImage(event) {
  if (event.target.src.includes('/grocery-card-image-v3.svg')) {
    return
  }

  event.target.src = productPlaceholderImage
}

watch(
  () => [
    props.product.id,
    props.product.deliveryTime,
    props.product.supplierAddress,
    props.product.supplierDetails?.customGoogleAddress,
    props.product.supplierDetails?.custom_google_address,
    deliveryLocationVersion.value,
  ],
  updateDeliveryTimeLabel,
  { immediate: true },
)
</script>

<template>
  <article
    class="product-card"
    :class="{ 'is-compact': compact, 'is-out-of-stock': isOutOfStock }"
  >
    <button
      class="product-wishlist-button"
      :class="{ 'is-active': isWishlisted }"
      type="button"
      :aria-label="isWishlisted ? `Remove ${product.name} from wishlist` : `Add ${product.name} to wishlist`"
      :aria-pressed="isWishlisted"
      @keydown.stop
      @mousedown.stop
      @pointerdown.stop
      @click.stop.prevent="handleWishlistToggle"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z" />
      </svg>
    </button>

    <div
      class="product-image product-select-area"
      tabindex="-1"
      aria-hidden="true"
      @click="selectProduct"
    >
      <img
        :src="product.image || productPlaceholderImage"
        alt=""
        loading="lazy"
        decoding="async"
        width="252"
        height="160"
        @error="showPlaceholderImage"
      />
      <span v-if="deliveryTimeLabel" class="product-badge">{{ deliveryTimeLabel }}</span>
    </div>

    <div class="product-info">
      <div
        class="product-summary product-select-area"
        tabindex="0"
        role="button"
        :aria-label="`View ${product.name} details`"
        @click="selectProduct"
        @keydown.enter="selectProduct"
        @keydown.space.prevent="selectProduct"
      >
        <div v-if="product.category" class="product-meta">
          <p class="product-category">{{ product.category }}</p>
        </div>
        <h2 class="product-name" :title="product.name">{{ product.name }}</h2>
        <p v-if="supplierName" class="product-supplier" :title="supplierName">
          {{ supplierName }}
        </p>
        <div class="product-card-details">
          <template v-if="hasRating">
            <span class="product-card-rating" :aria-label="`Rated ${rating} out of 5`">★ {{ rating }}</span>
            <span class="product-card-reviews">{{ reviewLabel }}</span>
          </template>
          <span
            v-if="!isRfqOnly"
            class="product-card-stock"
            :class="{ 'is-out': isOutOfStock, 'is-low': isLowStock }"
          >
            {{ stockLabel }}
          </span>
        </div>
      </div>

      <div class="product-footer">
        <span class="product-price">
          AED {{ formattedPrice }}
        </span>

        <div
          v-if="cartQuantity"
          class="product-quantity-control"
          role="group"
          :aria-label="`${product.name} quantity`"
        >
          <button
            type="button"
            :aria-label="cartQuantity === 1 ? `Remove ${product.name} from cart` : `Decrease ${product.name} quantity`"
            @click.stop="decreaseCartQuantity"
          >
            −
          </button>
          <span aria-live="polite">{{ cartQuantity }}</span>
          <button
            type="button"
            :aria-label="`Increase ${product.name} quantity`"
            :disabled="!canIncreaseQuantity"
            :title="canIncreaseQuantity ? '' : 'No more stock available'"
            @click.stop="increaseCartQuantity"
          >
            +
          </button>
        </div>
        <button
          v-else-if="isRfqOnly"
          class="add-cart-button is-rfq"
          type="button"
          :aria-label="`Request quotation for ${product.name}`"
          @click.stop="handleAddToCart"
        >
          <span>Request Quotation</span>
        </button>
        <button
          v-else
          class="add-cart-button"
          type="button"
          :aria-label="isOutOfStock ? `${product.name} is out of stock` : `Add ${product.name} to cart`"
          :disabled="isOutOfStock"
          @click.stop="handleAddToCart"
        >
          {{ isOutOfStock ? 'SOLD OUT' : 'ADD TO CART' }}
        </button>
      </div>
    </div>
  </article>
</template>
