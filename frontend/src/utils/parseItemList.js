const HEADER_NAMES = new Set(['item', 'items', 'item name', 'name', 'product', 'products', 'product name'])
const BULLET_PREFIX = /^(?:[-*•·–]+|\d+[.)])\s*/
const QUANTITY_UNITS = 'x|kgs?|kilos?|gms?|grams?|g|ltrs?|litres?|liters?|ml|l|pcs?|pieces?|packs?|packets?|box(?:es)?|bottles?|dozen'
const QUANTITY_PREFIX = new RegExp(`^\\d+(?:\\.\\d+)?(?:\\s*(?:${QUANTITY_UNITS})\\b|\\s)\\s*(?:(?:x|of)\\b)?\\s*`, 'i')
const QUANTITY_SUFFIX = new RegExp(`[\\s:(-]+(?:x\\s*)?\\d+(?:\\.\\d+)?\\s*(?:(?:${QUANTITY_UNITS})\\b)?\\)?$`, 'i')

function cleanListEntry(entry) {
  const withoutBullet = entry.trim().replace(/^"|"$/g, '').trim().replace(BULLET_PREFIX, '')
  const itemName = withoutBullet.replace(QUANTITY_PREFIX, '').replace(QUANTITY_SUFFIX, '').trim()

  return itemName || withoutBullet.trim()
}

function collectListEntries(rawEntries, { skipHeader = false } = {}) {
  const uniqueEntries = new Map()

  rawEntries.map(cleanListEntry).forEach((entry, index) => {
    const entryKey = entry.toLowerCase()
    const isHeader = skipHeader && index === 0 && HEADER_NAMES.has(entryKey)

    if (entry && !/^[\d.]+$/.test(entry) && !isHeader && !uniqueEntries.has(entryKey)) {
      uniqueEntries.set(entryKey, entry)
    }
  })

  return Array.from(uniqueEntries.values())
}

// A typed list has one item per row, so a comma stays part of the item.
export function parseItemRows(text) {
  return collectListEntries(text.split(/\r?\n/))
}

// A CSV keeps its item name in the first column; a text file may also separate items with commas.
export function parseItemList(fileText, { isCsv = false } = {}) {
  const lines = fileText.replace(/^\uFEFF/, '').split(/\r?\n/)

  return isCsv
    ? collectListEntries(lines.map((line) => line.split(/[,;\t]/)[0]), { skipHeader: true })
    : collectListEntries(lines.flatMap((line) => line.split(/[,;\t]/)))
}

export function getSingularSearchTerm(term) {
  if (/oes$/i.test(term)) {
    return term.slice(0, -2)
  }

  if (/ies$/i.test(term)) {
    return `${term.slice(0, -3)}y`
  }

  return /[^s]s$/i.test(term) ? term.slice(0, -1) : ''
}
