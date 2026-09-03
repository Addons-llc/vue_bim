<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LOCATION_UPDATED_EVENT, getEstimatedDeliveryTimeLabel } from '../../api/deliveryEta'
import { customerAddresses } from '../../data/addressStore'
import {
  addProductToCart,
  cartProducts,
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

const cartItem = computed(() => cartProducts.value.find((item) => item.id === props.product.id))
const cartQuantity = computed(() => cartItem.value?.quantity || 0)
const isWishlisted = computed(() => isProductWishlisted(props.product.id))
const productPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`
const isRfqOnly = computed(() => props.product.customRfqOnly === true)
const availableQuantity = computed(() => {
  const quantity = Number(props.product.customAvailableQty ?? props.product.stockQuantity ?? 0)

  return Number.isFinite(quantity) ? quantity : 0
})
const isOutOfStock = computed(() => props.product.inStock === false)
const stockLabel = computed(() => (isOutOfStock.value ? 'Out of stock' : `${availableQuantity.value} in stock`))
const supplierName = computed(() =>
  props.product.supplierName || props.product.supplier || '',
)
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
const reviewLabel = computed(() => {
  const reviewCount = props.product.reviewCount || 0

  return reviewCount === 1 ? '1 review' : `${reviewCount} reviews`
})
const deliveryTimeLabel = ref(props.product.deliveryTime || '')

async function updateDeliveryTimeLabel() {
  deliveryTimeLabel.value = await getEstimatedDeliveryTimeLabel(props.product)
}

function handleAddToCart() {
  addProductToCart({
    ...props.product,
    selectedSize: defaultProductSize.value,
  })
}

function decreaseCartQuantity() {
  updateCartProductQuantity(props.product.id, cartQuantity.value - 1)
}

function handleWishlistToggle() {
  toggleProductWishlist(props.product)
}

function handleRequestQuotation() {
  handleAddToCart()
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

onMounted(() => {
  updateDeliveryTimeLabel()
  window.addEventListener(LOCATION_UPDATED_EVENT, updateDeliveryTimeLabel)
})

onBeforeUnmount(() => {
  window.removeEventListener(LOCATION_UPDATED_EVENT, updateDeliveryTimeLabel)
})

watch(
  () => [
    props.product.id,
    props.product.deliveryTime,
    props.product.supplierAddress,
    props.product.supplierDetails?.customGoogleAddress,
    props.product.supplierDetails?.custom_google_address,
  ],
  () => {
    updateDeliveryTimeLabel()
  },
  { immediate: true },
)

watch(
  customerAddresses,
  () => {
    updateDeliveryTimeLabel()
  },
  { deep: true },
)

</script>

<template>
  <article
    class="product-card"
    :class="{ 'is-compact': compact }"
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
      tabindex="0"
      role="button"
      :aria-label="`View ${product.name} details`"
      @click="selectProduct"
      @keydown.enter="selectProduct"
      @keydown.space.prevent="selectProduct"
    >
      <img
        :src="product.image || productPlaceholderImage"
        :alt="product.name"
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
        <div class="product-meta">
          <p class="product-category">{{ product.category }}</p>
          <span class="product-rating">★ {{ product.rating }}</span>
        </div>
        <h2 class="product-name">{{ product.name }}</h2>
        <p v-if="supplierName" class="product-supplier">
          {{ supplierName }}
        </p>
        <div class="product-card-details">
          <span class="product-card-rating">★ {{ product.rating }}</span>
          <span class="product-card-reviews">{{ reviewLabel }}</span>
          <span
            class="product-card-stock"
            :class="{ 'is-out': isOutOfStock }"
          >
            {{ stockLabel }}
          </span>
        </div>
      </div>

      <div class="product-footer">
        <span class="product-price">
          AED {{ product.price }}
        </span>
        <div v-if="isRfqOnly" class="product-rfq-actions">
          <div
            v-if="cartQuantity"
            class="product-quantity-control"
            :aria-label="`${product.name} quantity`"
          >
            <button
              type="button"
              :aria-label="`Decrease ${product.name} quantity`"
              @click.stop="decreaseCartQuantity"
            >
              -
            </button>
            <span>{{ cartQuantity }}</span>
            <button
              type="button"
              :aria-label="`Increase ${product.name} quantity`"
              @click.stop="handleAddToCart"
            >
              +
            </button>
          </div>
          <button
            v-else
            class="add-cart-button is-rfq"
            type="button"
            :aria-label="`Request quotation for ${product.name}`"
            @click.stop="handleRequestQuotation"
          >
            <span>Request Quotation</span>
          </button>
        </div>
        <template v-else>
          <div
            v-if="cartQuantity"
            class="product-quantity-control"
            :aria-label="`${product.name} quantity`"
          >
            <button
              type="button"
              :aria-label="`Decrease ${product.name} quantity`"
              @click.stop="decreaseCartQuantity"
            >
              -
            </button>
            <span>{{ cartQuantity }}</span>
            <button
              type="button"
              :aria-label="`Increase ${product.name} quantity`"
              @click.stop="handleAddToCart"
            >
              +
            </button>
          </div>
          <button
            v-else
            class="add-cart-button"
            type="button"
            :aria-label="`Add ${product.name} to cart`"
            :disabled="isOutOfStock"
            @click.stop="handleAddToCart"
          >
            ADD TO CART
          </button>
        </template>
      </div>
    </div>
  </article>
</template>
