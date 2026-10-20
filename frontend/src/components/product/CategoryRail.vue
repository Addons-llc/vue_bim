<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  activeCategory: {
    type: String,
    default: '',
  },
  categories: {
    type: Array,
    required: true,
  },
  title: {
    type: String,
    default: 'Categories',
  },
  viewAllTo: {
    type: [String, Object],
    default: '',
  },
  viewAllLabel: {
    type: String,
    default: 'View all',
  },
  showViewAllButton: {
    type: Boolean,
    default: false,
  },
  sectionId: {
    type: String,
    default: '',
  },
  horizontal: {
    type: Boolean,
    default: false,
  },
  itemType: {
    type: String,
    default: 'category',
  },
  iconGrid: {
    type: Boolean,
    default: false,
  },
  showBrandDetailFallbacks: {
    type: Boolean,
    default: false,
  },
  stackedTile: {
    type: Boolean,
    default: false,
  },
  // Show only the tiles that fully fit in one row (no horizontal scroll); "View all" leads to the rest.
  fitToRow: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select', 'view-all'])

const categoryPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`
const gridElement = ref(null)
const fittingCount = ref(null)
let gridResizeObserver = null

const visibleCategories = computed(() => {
  if (!props.fitToRow || fittingCount.value === null) {
    return props.categories
  }

  return props.categories.slice(0, fittingCount.value)
})

async function measureFittingCount() {
  if (!props.fitToRow || !gridElement.value) {
    return
  }

  // Render every tile first so the measurement reflects the current tile widths for this breakpoint.
  fittingCount.value = null
  await nextTick()

  const grid = gridElement.value
  if (!grid) {
    return
  }

  const gridRight = grid.getBoundingClientRect().right
  const tiles = Array.from(grid.children)
  const fittingTiles = tiles.filter((tile) => tile.getBoundingClientRect().right <= gridRight + 1)

  fittingCount.value = Math.max(fittingTiles.length, 1)
}

onMounted(() => {
  if (!props.fitToRow || typeof ResizeObserver === 'undefined') {
    return
  }

  let lastWidth = 0
  gridResizeObserver = new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width)

    if (width !== lastWidth) {
      lastWidth = width
      measureFittingCount()
    }
  })
  gridResizeObserver.observe(gridElement.value)
})

onUnmounted(() => {
  gridResizeObserver?.disconnect()
})

watch(() => props.categories, measureFittingCount)

function showPlaceholderImage(event) {
  if (event.target.src.includes('/grocery-card-image-v3.svg')) {
    return
  }

  event.target.src = categoryPlaceholderImage
}

function getCategoryImage(category) {
  return category.image || categoryPlaceholderImage
}

function selectCategory(category) {
  emit('select', category)
}

function viewAll() {
  emit('view-all')
}
</script>

<template>
  <section
    class="category-section"
    :class="[`category-section--${itemType}`, { 'is-icon-grid': iconGrid }]"
    :id="sectionId || undefined"
  >
    <div class="category-section-heading">
      <h2>{{ title }}</h2>
      <RouterLink
        v-if="viewAllTo"
        class="section-link category-view-all-link"
        :to="viewAllTo"
      >
        {{ viewAllLabel }}
      </RouterLink>
      <button
        v-else-if="showViewAllButton"
        class="section-link category-view-all-link"
        type="button"
        @click="viewAll"
      >
        {{ viewAllLabel }}
      </button>
    </div>
    <div
      ref="gridElement"
      class="category-grid"
      :class="{ 'is-manual-scroll': horizontal }"
    >
      <button
        v-for="category in visibleCategories"
        :key="category.id"
        class="category-tile"
        :class="{
          'is-active': activeCategory === category.name,
          'is-stacked': stackedTile,
        }"
        type="button"
        @click="selectCategory(category)"
      >
        <span class="category-image-wrap">
          <img
            class="category-image"
            :src="getCategoryImage(category)"
            :alt="category.name"
            @error="showPlaceholderImage"
          />
        </span>
        <span class="category-copy">
          <span class="category-name">{{ category.name }}</span>
        </span>
      </button>
    </div>
  </section>
</template>
