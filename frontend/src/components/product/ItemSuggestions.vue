<script setup>
import { productRoute } from '../../utils/productRoute'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getItemSuggestions } from '../../api/itemApi'
import { saveSelectedProduct } from '../../data/productSelectionStore'
import ProductCard from './ProductCard.vue'

const props = defineProps({
  // Item codes of the selected items (e.g. the cart) to base suggestions on.
  itemCodes: {
    type: Array,
    required: true,
  },
  title: {
    type: String,
    default: 'You may also like',
  },
})

const router = useRouter()
const suggestions = ref([])
let requestId = 0

// Re-fetch only when the set of items changes, not on quantity changes.
const itemCodesKey = computed(() =>
  [...new Set(props.itemCodes.filter(Boolean))].sort().join('|'),
)

async function loadSuggestions() {
  const currentRequestId = ++requestId
  const codes = itemCodesKey.value ? itemCodesKey.value.split('|') : []

  if (!codes.length) {
    suggestions.value = []
    return
  }

  try {
    const loadedSuggestions = await getItemSuggestions(codes)

    if (currentRequestId === requestId) {
      // Hide anything already selected (e.g. added to the cart from this rail).
      suggestions.value = loadedSuggestions.filter((product) =>
        !codes.includes(product.itemCode) && !codes.includes(product.id),
      )
    }
  } catch {
    if (currentRequestId === requestId) {
      suggestions.value = []
    }
  }
}

function openProduct(product) {
  saveSelectedProduct(product)
  router.push(productRoute(product))
}

watch(itemCodesKey, loadSuggestions, { immediate: true })
</script>

<template>
  <section v-if="suggestions.length" class="item-suggestions" aria-labelledby="item-suggestions-title">
    <h2 id="item-suggestions-title" class="item-suggestions-title">{{ title }}</h2>
    <div class="product-rail item-suggestions-rail">
      <ProductCard
        v-for="product in suggestions"
        :key="product.id"
        :product="product"
        compact
        @select="openProduct(product)"
      />
    </div>
  </section>
</template>
