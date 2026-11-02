import { computed, ref } from 'vue'
import { getProducts } from '../api/productApi'
import { getSingularSearchTerm, parseItemList, parseItemRows } from '../utils/parseItemList'

const MAX_LIST_ITEMS = 30
const MAX_LIST_FILE_SIZE = 1024 * 1024
const RESULTS_PER_LIST_ITEM = 8
const LIST_SEARCHES_AT_ONCE = 4

// Kept outside the composable so the list survives opening a product and coming back.
const listText = ref('')
const listEntries = ref([])
const listError = ref('')
const skippedListItemCount = ref(0)
let listRequestId = 0

async function searchPublishedProducts(term) {
  const products = await getProducts({
    limit_page_length: RESULTS_PER_LIST_ITEM,
    search: term,
  })

  return products.filter((product) => product.isPublished !== false)
}

async function findListEntryProducts(term) {
  const products = await searchPublishedProducts(term)
  const singularTerm = getSingularSearchTerm(term)

  return products.length || !singularTerm ? products : searchPublishedProducts(singularTerm)
}

function updateListEntry(term, changes) {
  listEntries.value = listEntries.value.map((entry) =>
    entry.term === term ? { ...entry, ...changes } : entry,
  )
}

async function searchListEntries(terms, requestId) {
  const pendingTerms = [...terms]

  async function searchNextTerm() {
    while (pendingTerms.length && requestId === listRequestId) {
      const term = pendingTerms.shift()

      try {
        const products = await findListEntryProducts(term)

        if (requestId === listRequestId) {
          updateListEntry(term, { isLoading: false, products })
        }
      } catch {
        if (requestId === listRequestId) {
          updateListEntry(term, { hasFailed: true, isLoading: false })
        }
      }
    }
  }

  await Promise.all(Array.from({ length: LIST_SEARCHES_AT_ONCE }, searchNextTerm))
}

function clearListResults() {
  listRequestId += 1
  listEntries.value = []
  listError.value = ''
  skippedListItemCount.value = 0
}

export function useSearchList() {
  const listItemCount = computed(() => parseItemRows(listText.value).length)
  const isLoadingList = computed(() => listEntries.value.some((entry) => entry.isLoading))
  const foundListEntries = computed(() =>
    listEntries.value.filter((entry) => entry.products.length),
  )
  const missingListEntries = computed(() =>
    listEntries.value.filter((entry) => !entry.isLoading && !entry.hasFailed && !entry.products.length),
  )
  const failedListEntries = computed(() => listEntries.value.filter((entry) => entry.hasFailed))

  function clearList() {
    clearListResults()
    listText.value = ''
  }

  // Adds the file's items to the box, so anything already typed is kept.
  async function addListFile(file) {
    const isCsv = /\.csv$/i.test(file.name)

    listError.value = ''

    if (!isCsv && !/\.txt$/i.test(file.name)) {
      listError.value = 'Please upload a .txt or .csv file.'
      return
    }

    if (file.size > MAX_LIST_FILE_SIZE) {
      listError.value = 'This file is too large. Please upload a list under 1 MB.'
      return
    }

    try {
      const fileText = await file.text()
      const fileItems = fileText.includes('\0') ? [] : parseItemList(fileText, { isCsv })

      if (!fileItems.length) {
        listError.value = 'We could not find any items in this file. Put one item on each line.'
        return
      }

      listText.value = [listText.value.trim(), ...fileItems].filter(Boolean).join('\n')
    } catch {
      listError.value = 'We could not read this file. Please try again.'
    }
  }

  async function submitList() {
    const items = parseItemRows(listText.value)
    const listTerms = items.slice(0, MAX_LIST_ITEMS)

    clearListResults()
    skippedListItemCount.value = items.length - listTerms.length
    listEntries.value = listTerms.map((term) => ({
      hasFailed: false,
      isLoading: true,
      products: [],
      term,
    }))
    await searchListEntries(listTerms, listRequestId)
  }

  return {
    addListFile,
    clearList,
    failedListEntries,
    foundListEntries,
    isLoadingList,
    listEntries,
    listError,
    listItemCount,
    listText,
    missingListEntries,
    skippedListItemCount,
    submitList,
  }
}
