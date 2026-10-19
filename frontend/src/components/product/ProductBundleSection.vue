<script setup>
import {
  addProductToCart,
  cartQuantityById,
  updateCartProductQuantity,
} from '../../data/cartStore'

defineProps({
  bundles: {
    type: Array,
    required: true,
  },
  title: {
    type: String,
    default: 'Weekly Vegetable Kits',
  },
  subtitle: {
    type: String,
    default: 'Fresh picks bundled for the week, at a better price',
  },
  sectionId: {
    type: String,
    default: 'weekly-kits',
  },
})

const emit = defineEmits(['select'])

const VISIBLE_BUNDLE_ITEMS = 4
const bundlePlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`
const priceFormatter = new Intl.NumberFormat('en-AE', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

function formatPrice(value) {
  const price = Number(value)

  return Number.isFinite(price) ? priceFormatter.format(price) : value
}

function formatQuantity(component) {
  const qty = Number(component.qty) || 0
  const qtyLabel = Number.isInteger(qty) ? qty : priceFormatter.format(qty)

  return component.uom ? `${qtyLabel} ${component.uom}` : `× ${qtyLabel}`
}

function getSavings(bundle) {
  return bundle.oldPrice ? bundle.oldPrice - bundle.price : 0
}

function getCartQuantity(bundle) {
  return cartQuantityById.value.get(bundle.id) || 0
}

function addBundleToCart(bundle) {
  if (bundle.inStock === false) {
    return
  }

  addProductToCart(bundle)
}

function decreaseBundleQuantity(bundle) {
  updateCartProductQuantity(bundle.id, getCartQuantity(bundle) - 1)
}

function selectBundle(bundle) {
  emit('select', bundle)
}

function showPlaceholderImage(event) {
  if (event.target.src.includes('/grocery-card-image-v3.svg')) {
    return
  }

  event.target.src = bundlePlaceholderImage
}
</script>

<template>
  <section class="bundle-section" :id="sectionId || undefined">
    <div class="bundle-section-heading">
      <h2>{{ title }}</h2>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>

    <div class="bundle-rail">
      <article
        v-for="bundle in bundles"
        :key="bundle.id"
        class="bundle-card"
        :class="{ 'is-out-of-stock': bundle.inStock === false }"
      >
        <div class="bundle-card-media" aria-hidden="true" @click="selectBundle(bundle)">
          <img
            :src="bundle.image || bundlePlaceholderImage"
            alt=""
            loading="lazy"
            decoding="async"
            @error="showPlaceholderImage"
          />
          <span class="bundle-card-count">
            {{ bundle.bundleItems.length }} {{ bundle.bundleItems.length === 1 ? 'item' : 'items' }}
          </span>
          <span v-if="getSavings(bundle) > 0" class="bundle-card-savings">
            Save AED {{ formatPrice(getSavings(bundle)) }}
          </span>
        </div>

        <div class="bundle-card-body">
          <h3
            class="bundle-card-title"
            tabindex="0"
            role="button"
            :title="bundle.name"
            @click="selectBundle(bundle)"
            @keydown.enter="selectBundle(bundle)"
            @keydown.space.prevent="selectBundle(bundle)"
          >
            {{ bundle.name }}
          </h3>
          <p v-if="bundle.supplierName" class="bundle-card-supplier">{{ bundle.supplierName }}</p>

          <ul v-if="bundle.bundleItems.length" class="bundle-card-contents" aria-label="Kit contents">
            <li
              v-for="component in bundle.bundleItems.slice(0, VISIBLE_BUNDLE_ITEMS)"
              :key="component.itemCode"
            >
              <span class="bundle-content-name">{{ component.name }}</span>
              <span class="bundle-content-qty">{{ formatQuantity(component) }}</span>
            </li>
            <li v-if="bundle.bundleItems.length > VISIBLE_BUNDLE_ITEMS" class="bundle-content-more">
              + {{ bundle.bundleItems.length - VISIBLE_BUNDLE_ITEMS }} more
            </li>
          </ul>

          <div class="bundle-card-footer">
            <span class="bundle-card-price">
              <span v-if="bundle.oldPrice" class="bundle-card-old-price">
                AED {{ formatPrice(bundle.oldPrice) }}
              </span>
              AED {{ formatPrice(bundle.price) }}
            </span>

            <div
              v-if="getCartQuantity(bundle)"
              class="product-quantity-control"
              role="group"
              :aria-label="`${bundle.name} quantity`"
            >
              <button
                type="button"
                :aria-label="getCartQuantity(bundle) === 1 ? `Remove ${bundle.name} from cart` : `Decrease ${bundle.name} quantity`"
                @click="decreaseBundleQuantity(bundle)"
              >
                −
              </button>
              <span aria-live="polite">{{ getCartQuantity(bundle) }}</span>
              <button
                type="button"
                :aria-label="`Increase ${bundle.name} quantity`"
                @click="addBundleToCart(bundle)"
              >
                +
              </button>
            </div>
            <button
              v-else
              class="add-cart-button"
              type="button"
              :disabled="bundle.inStock === false"
              :aria-label="bundle.inStock === false ? `${bundle.name} is out of stock` : `Add ${bundle.name} to cart`"
              @click="addBundleToCart(bundle)"
            >
              {{ bundle.inStock === false ? 'SOLD OUT' : 'ADD KIT' }}
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
