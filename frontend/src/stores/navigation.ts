import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getCategories, createCategory, updateCategory, deleteCategory, sortCategories,
  getWebsites, createWebsite, updateWebsite, deleteWebsite, sortWebsites,
  searchNavigation, recordVisit as recordVisitApi
} from '../api'

export interface Website {
  id: number
  name: string
  url: string
  icon_url: string
  description: string
  category_id: number
  sort_order: number
  is_pinned: boolean
  is_favorite: boolean
  notes: string
  visit_count: number
  last_visited: string | null
}

export interface Category {
  id: number
  name: string
  icon: string
  sort_order: number
  is_default: boolean
  website_count: number
}

export const useNavigationStore = defineStore('navigation', () => {
  const categories = ref<Category[]>([])
  const websites = ref<Website[]>([])
  const loading = ref(false)
  const searchResults = ref<{ websites: Website[]; categories: Category[] }>({ websites: [], categories: [] })

  const websitesByCategory = computed(() => {
    const map: Record<number, Website[]> = {}
    for (const w of websites.value) {
      if (!map[w.category_id]) map[w.category_id] = []
      map[w.category_id].push(w)
    }
    return map
  })

  async function fetchCategories() {
    const { data } = await getCategories()
    categories.value = data
  }

  async function fetchWebsites(categoryId?: number) {
    const { data } = await getWebsites(categoryId)
    if (categoryId !== undefined) {
      const others = websites.value.filter(w => w.category_id !== categoryId)
      websites.value = [...others, ...data]
    } else {
      websites.value = data
    }
  }

  async function fetchAll() {
    loading.value = true
    await Promise.all([fetchCategories(), fetchWebsites()])
    loading.value = false
  }

  async function addCategory(data: { name: string; icon?: string }) {
    const { data: cat } = await createCategory(data)
    categories.value.push(cat)
    categories.value.sort((a, b) => a.sort_order - b.sort_order)
    return cat
  }

  async function editCategory(id: number, data: any) {
    await updateCategory(id, data)
    await fetchCategories()
  }

  async function removeCategory(id: number) {
    await deleteCategory(id)
    categories.value = categories.value.filter(c => c.id !== id)
    websites.value = websites.value.filter(w => w.category_id !== id)
  }

  async function reorderCategories(items: { id: number; sort_order: number }[]) {
    await sortCategories(items)
    await fetchCategories()
  }

  async function addWebsite(data: any) {
    const { data: web } = await createWebsite(data)
    websites.value.push(web)
    return web
  }

  async function editWebsite(id: number, data: any) {
    await updateWebsite(id, data)
    await fetchWebsites()
  }

  async function removeWebsite(id: number) {
    await deleteWebsite(id)
    websites.value = websites.value.filter(w => w.id !== id)
  }

  async function reorderWebsites(items: { id: number; sort_order: number; category_id?: number }[]) {
    await sortWebsites(items)
    await fetchAll()
  }

  async function search(q: string) {
    const { data } = await searchNavigation(q)
    searchResults.value = data
  }

  async function recordVisit(id: number) {
    await recordVisitApi(id)
  }

  return {
    categories, websites, loading, searchResults, websitesByCategory,
    fetchCategories, fetchWebsites, fetchAll,
    addCategory, editCategory, removeCategory, reorderCategories,
    addWebsite, editWebsite, removeWebsite, reorderWebsites,
    search, recordVisit
  }
})
