<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  addProductToCart,
  cartQuantityById,
  updateCartProductQuantity,
} from '../../data/cartStore'

const props = defineProps({
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
  // Optional route for an "Explore" link beside the title.
  viewAllTo: {
    type: [String, Object],
    default: null,
  },
  viewAllLabel: {
    type: String,
    default: 'Explore',
  },
  // Show only the cards that fully fit in one row (no horizontal scroll). The
  // default slot receives `extraLimit`: how many of its cards it may render.
  fitToRow: {
    type: Boolean,
    default: false,
  },
  // Number of cards the default slot would render without a limit.
  extraCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['select'])

const railElement = ref(null)
const fittingCount = ref(null)
let railResizeObserver = null

const totalCount = computed(() => props.bundles.length + props.extraCount)
const visibleBundles = computed(() =>
  !props.fitToRow || fittingCount.value === null
    ? props.bundles
    : props.bundles.slice(0, fittingCount.value),
)
const extraLimit = computed(() =>
  !props.fitToRow || fittingCount.value === null
    ? null
    : Math.max(fittingCount.value - props.bundles.length, 0),
)
const showViewAll = computed(() => {
  if (!props.viewAllTo) return false
  if (!props.fitToRow) return true

  return fittingCount.value !== null && fittingCount.value < totalCount.value
})

async function measureFittingCount() {
  if (!props.fitToRow || !railElement.value) {
    return
  }

  // Render every card first so the measurement uses this breakpoint's card widths.
  fittingCount.value = null
  await nextTick()

  const rail = railElement.value
  const cards = rail ? Array.from(rail.children) : []

  if (!cards.length) {
    return
  }

  const railRight = rail.getBoundingClientRect().right
  const firstRowBottom = cards[0].getBoundingClientRect().bottom
  const fittingCards = cards.filter((card) => {
    const rect = card.getBoundingClientRect()

    return rect.top < firstRowBottom && rect.right <= railRight + 1
  })

  fittingCount.value = Math.max(fittingCards.length, 1)
}

onMounted(() => {
  if (!props.fitToRow) {
    return
  }

  measureFittingCount()

  if (typeof ResizeObserver === 'undefined') {
    return
  }

  let lastWidth = 0
  railResizeObserver = new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width)

    if (width !== lastWidth) {
      lastWidth = width
      measureFittingCount()
    }
  })
  railResizeObserver.observe(railElement.value)
})

onUnmounted(() => {
  railResizeObserver?.disconnect()
})

watch(() => [props.bundles, props.extraCount], measureFittingCount)

const bundlePlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`
const priceFormatter = new Intl.NumberFormat('en-AE', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

function formatPrice(value) {
  const price = Number(value)

  return Number.isFinite(price) ? priceFormatter.format(price) : value
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
      <div class="bundle-section-heading-text">
        <h2>{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <RouterLink v-if="showViewAll" class="section-link home-explore-link" :to="viewAllTo">
        {{ viewAllLabel }}
      </RouterLink>
    </div>

    <div ref="railElement" class="bundle-rail" :class="{ 'is-fit-to-row': fitToRow }">
      <article
        v-for="bundle in visibleBundles"
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
              {{ bundle.inStock === false ? 'SOLD OUT' : 'ADD TO CART' }}
            </button>
          </div>
        </div>
      </article>

      <!-- Extra cards (e.g. products) shown in the same row after the bundles. -->
      <slot :extra-limit="extraLimit" />
    </div>
  </section>
</template>
