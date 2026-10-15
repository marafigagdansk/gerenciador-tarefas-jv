import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, getToken, setToken } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(getToken())
  const user = ref(null)
  const memberships = ref([])
  const canCreateCompany = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  function applyPayload(data) {
    user.value = data.user
    memberships.value = data.memberships
    canCreateCompany.value = data.can_create_company
  }

  function applySession(data) {
    token.value = data.token
    setToken(data.token)
    applyPayload(data)
  }

  async function setup(payload) {
    applySession(await api('/setup', { method: 'POST', body: payload }))
  }

  async function login(email, password) {
    applySession(await api('/auth/login', { method: 'POST', body: { email, password } }))
  }

  async function fetchMe() {
    applyPayload(await api('/auth/me'))
  }

  async function createCompany(payload) {
    applyPayload(await api('/companies', { method: 'POST', body: payload }))
  }

  async function updateCompany(companyId, payload) {
    applyPayload(await api(`/companies/${companyId}`, { method: 'PATCH', body: payload }))
  }

  async function deleteCompany(companyId) {
    applyPayload(await api(`/companies/${companyId}`, { method: 'DELETE' }))
  }

  function logout() {
    token.value = null
    user.value = null
    memberships.value = []
    canCreateCompany.value = false
    setToken(null)
  }

  return {
    token, user, memberships, canCreateCompany, isAuthenticated,
    setup, login, fetchMe, createCompany, updateCompany, deleteCompany, logout,
  }
})
