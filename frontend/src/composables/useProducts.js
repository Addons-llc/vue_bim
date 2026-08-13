import { computed, ref, unref, watch } from 'vue'
import {
  getCachedProductCategories,
  getProductCategories,
  getProducts,
} from '../api/productApi'

export function useProducts(searchText, initialCategory) {
  const PRODUCT_PAGE_SIZE = 48
  const products = ref([])
  const categories = ref(getCachedProductCategories())
  const isLoadingCategories = ref(false)
  const isLoadingProducts = ref(false)
  const isLoadingMoreProducts = ref(false)
  const hasMoreProducts = ref(false)
  const productError = ref('')
  const activeCategory = ref('')
  const activeProductQuery = ref({})
  const nextProductOffset = ref(0)
  let productRequestId = 0

  const isFilteredProducts = computed(() =>
    Boolean(activeCategory.value || unref(searchText).trim()),
  )

  const productSections = computed(() => {
    if (isFilteredProducts.value) {
      return [
        {
          id: 'filtered-products',
          title: activeCategory.value || 'Search results',
          products: products.value,
        },
      ]
    }

    const sectionMap = products.value.reduce((sections, product) => {
      const sectionName = product.category || 'Popular products'

      if (!sections.has(sectionName)) {
        sections.set(sectionName, {
          id: sectionName,
          title: sectionName,
          itemGroup: sectionName,
          products: [],
        })
      }

      sections.get(sectionName).products.push(product)

      return sections
    }, new Map())

    const sections = Array.from(sectionMap.values())
      .sort((firstSection, secondSection) =>
        firstSection.title.localeCompare(secondSection.title),
      )
      .map((section) => ({
        ...section,
        products: section.products.slice(0, 11),
      }))

    if (sections.length) {
      return sections
    }

    return [
      {
        id: 'popular-products',
        title: 'Popular products',
        products: products.value.slice(0, 8),
      },
    ]
  })

  const orderedCategories = computed(() => categories.value)

  async function loadCategories() {
    isLoadingCategories.value = !categories.value.length

    try {
      categories.value = await getProductCategories()
    } catch (error) {
      categories.value = []
      productError.value = error.message || 'Unable to load Item categories.'
    } finally {
      isLoadingCategories.value = false
    }
  }

  async function loadProducts(params = {}, { append = false } = {}) {
    const pageSize = params.limit_page_length || PRODUCT_PAGE_SIZE
    const query = {
      ...params,
      limit_page_length: pageSize,
      limit_start: append ? nextProductOffset.value : 0,
    }

    if (append) {
      if (isLoadingMoreProducts.value || !hasMoreProducts.value) {
        return
      }

      isLoadingMoreProducts.value = true
    } else {
      activeProductQuery.value = { ...params, limit_page_length: pageSize }
      nextProductOffset.value = 0
      hasMoreProducts.value = false
      isLoadingProducts.value = true
    }

    const requestId = ++productRequestId
    productError.value = ''

    try {
      const loadedProducts = await getProducts(query)

      if (requestId !== productRequestId) {
        return
      }

      products.value = append
        ? [...products.value, ...loadedProducts]
        : loadedProducts
      nextProductOffset.value = products.value.length
      hasMoreProducts.value = loadedProducts.length === pageSize
    } catch (error) {
      if (!append) {
        products.value = []
      }

      productError.value = error.message || 'Unable to load Item Master products.'
    } finally {
      if (requestId === productRequestId) {
        isLoadingProducts.value = false
        isLoadingMoreProducts.value = false
      }
    }
  }

  function loadHomeProducts() {
    loadCategories()

    return loadProducts({
      limit_page_length: PRODUCT_PAGE_SIZE,
    })
  }

  function loadMoreProducts() {
    return loadProducts(activeProductQuery.value, { append: true })
  }

  function selectCategory(category) {
    activeCategory.value = category.name

    return loadProducts({
      item_group: category.itemGroup || category.name,
      limit_page_length: PRODUCT_PAGE_SIZE,
    })
  }

  function selectProductSection(section) {
    activeCategory.value = section.title
    products.value = section.products
  }

  watch(
    () => [unref(searchText), unref(initialCategory)],
    ([searchValue, categoryValue]) => {
      const keyword = searchValue.trim()
      activeCategory.value = ''

      if (!keyword) {
        const category = categoryValue

        if (category) {
          loadCategories()
          selectCategory({ name: category, itemGroup: category })
          return
        }

        loadHomeProducts()
        return
      }

      loadProducts({
        limit_page_length: PRODUCT_PAGE_SIZE,
        search: keyword,
      })
    },
    {
      immediate: true,
    },
  )

  return {
    activeCategory,
    categories: orderedCategories,
    hasMoreProducts,
    isLoadingCategories,
    isFilteredProducts,
    isLoadingProducts,
    isLoadingMoreProducts,
    loadHomeProducts,
    loadMoreProducts,
    loadProducts,
    productError,
    products,
    productSections,
    selectCategory,
    selectProductSection,
  }
}
